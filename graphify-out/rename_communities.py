#!/usr/bin/env python3
"""
Rename communities in GRAPH_REPORT.md based on dominant project names.
Run after graphify update to get project names instead of "Community N".
"""

import json
import re
from pathlib import Path
from collections import Counter

def get_project_from_path(path: str) -> tuple:
    """Extract project name from source file path.

    Returns (project_name, is_project) where is_project=True if it's in a subdirectory.
    """
    if not path:
        return "", False
    parts = Path(path).parts
    # Root-level files (directly in workspace): use filename
    if len(parts) == 1:
        return Path(parts[0]).stem, False
    # Files in subdirectories: use subdirectory name
    if len(parts) >= 2:
        return parts[1], True
    return "", False

def analyze_communities(graph_path: str = "graphify-out/graph.json") -> dict:
    """Analyze graph.json and return community -> project mapping."""
    graph_file = Path(graph_path)

    if not graph_file.exists():
        print(f"Error: {graph_path} not found")
        return {}

    with open(graph_file) as f:
        data = json.load(f)

    community_projects: dict = {}
    community_root_files: dict = {}
    community_is_project: dict = {}

    for node in data.get("nodes", []):
        community = node.get("community")
        source_file = node.get("source_file", "")

        if community is None:
            continue

        project, is_project = get_project_from_path(source_file)
        if not project:
            continue

        if community not in community_projects:
            community_projects[community] = []
            community_is_project[community] = is_project

        community_projects[community].append((project, is_project))

    # For each community, find the most common project
    community_names = {}
    for community, projects in community_projects.items():
        if projects:
            # Count project names, preferring subdirectory projects over root files
            project_counts = {}
            for name, is_p in projects:
                if is_p:
                    # Project files get higher weight
                    project_counts[name] = project_counts.get(name, 0) + 3
                else:
                    project_counts[name] = project_counts.get(name, 0) + 1

            most_common = max(project_counts.items(), key=lambda x: x[1])[0]
            community_names[community] = most_common
        else:
            community_names[community] = ""

    return community_names

def update_graph_json(
    graph_path: str = "graphify-out/graph.json",
    community_names: dict = None
):
    """Update community_name in graph.json for all nodes."""
    if community_names is None:
        community_names = analyze_communities(graph_path)

    graph_file = Path(graph_path)
    if not graph_file.exists():
        print(f"Warning: {graph_path} not found, skipping graph.json update")
        return

    with open(graph_file) as f:
        data = json.load(f)

    updated_count = 0
    for node in data.get("nodes", []):
        community = node.get("community")
        if community in community_names and community_names[community]:
            old_name = node.get("community_name", "")
            new_name = community_names[community]
            if old_name != new_name:
                node["community_name"] = new_name
                updated_count += 1

    with open(graph_file, "w") as f:
        json.dump(data, f)

    print(f"Updated {updated_count} nodes in {graph_path}")

def update_graph_html(
    html_path: str = "graphify-out/graph.html",
    community_names: dict = None,
    graph_path: str = "graphify-out/graph.json"
):
    """Update community_name in graph.html for all nodes."""
    if community_names is None:
        community_names = analyze_communities(graph_path)

    html_file = Path(html_path)
    if not html_file.exists():
        print(f"Warning: {html_path} not found, skipping HTML update")
        return

    content = html_file.read_text()

    # Replace "Community N" with project name in the embedded data
    # Pattern: "community_name": "Community N"
    updated_count = 0
    for comm_num, project_name in community_names.items():
        if project_name:
            # Match "Community N" where N is the community number
            pattern = f'"community_name": "Community {comm_num}"'
            replacement = f'"community_name": "{project_name}"'
            if pattern in content:
                content = content.replace(pattern, replacement)
                updated_count += 1

    html_file.write_text(content)
    print(f"Updated {updated_count} community names in {html_path}")

def update_graph_report(
    report_path: str = "graphify-out/GRAPH_REPORT.md",
    graph_path: str = "graphify-out/graph.json"
):
    """Update GRAPH_REPORT.md with project names instead of 'Community N'."""

    community_names = analyze_communities(graph_path)

    # Also update graph.html with project names
    update_graph_html(community_names=community_names, graph_path=graph_path)

    report_file = Path(report_path)
    if not report_file.exists():
        print(f"Error: {report_path} not found")
        return

    content = report_file.read_text()

    # Replace "Community N" with "ПроектName"
    # Pattern: ### Community N - "Community N"
    def replace_community(match):
        community_num = int(match.group(1))
        if community_num in community_names and community_names[community_num]:
            return f"### Community {community_num} - {community_names[community_num]}"
        return match.group(0)

    # Also handle the navigation links
    # [[_COMMUNITY_Community N|Community N]]
    content = re.sub(
        r'\[\[\[]_COMMUNITY_Community (\d+)[\|]Community \d+[\]]',
        lambda m: f"[[_COMMUNITY_{m.group(1)}|Community {m.group(1)}]]",
        content
    )

    # Replace section headers: ### Community N - "Community N"
    content = re.sub(
        r'^### Community (\d+) - "Community \d+"$',
        replace_community,
        content,
        flags=re.MULTILINE
    )

    # Replace standalone: ### Community N
    content = re.sub(
        r'^### Community (\d+) - "Community \d+"$',
        replace_community,
        content,
        flags=re.MULTILINE
    )

    report_file.write_text(content)
    print(f"Updated {report_path}")

    # Print summary
    print("\nCommunity -> Project mapping:")
    for comm in sorted(community_names.keys()):
        print(f"  Community {comm}: {community_names[comm]}")

    return community_names

if __name__ == "__main__":
    import sys
    report_path = sys.argv[1] if len(sys.argv) > 1 else "graphify-out/GRAPH_REPORT.md"
    graph_path = sys.argv[2] if len(sys.argv) > 2 else "graphify-out/graph.json"

    update_graph_report(report_path, graph_path)