"""
IMPORTANT: In order to execute this file, the Edge Cluster Frontend Engine must be running as the docs are generated using a SM object.

Create State Machine documentation using a `DeviceRuntimeStateMachine` object.
It uses the DOT Language, which is a plain text graph description language.
Output files will be generated in the path defined by 'OUTPUT_FILENAME' variable.
Output files:
    - Markdown file containing all the information about the state machine: States, Transitions and the state diagram written in DOT Language
    - PNG file containig only the state diagram written in DOT Language.

Pre-requisites:
    - graphviz
        - `sudo apt install graphviz`

Additional information:
    - [DOT Language information](https://graphviz.org/doc/info/lang.html) 
    - [graphviz documentation](https://graphviz.org/docs/attrs/shape/)
    - [Online graphviz visualization tool](https://dreampuf.github.io/GraphvizOnline)
"""

import os
import sys
import graphviz

sys.path.append(".")
from cognit.modules._device_runtime_state_machine import DeviceRuntimeStateMachine

OUTPUT_DIR = "docs/stateMachine"  # 2 files will be generated with this name: A markdown file and a PNG file
OUTPUT_MARKDOWN_FILEPATH = f"{OUTPUT_DIR}/device_runtime_sm.md"
OUTPUT_SIMPLE_CHART_FILEPATH = f"{OUTPUT_DIR}/device_runtime_sm_simple" # do not put ".png" here as it is added later
OUTPUT_DETAILED_CHART_FILEPATH = f"{OUTPUT_DIR}/device_runtime_sm_detailed.png"

# “dot” refers to the DOT language, which is a plain text graph description language
def generate_dot_format(sm):
    dot = ["digraph G {"]
    dot.append("    rankdir=LR;")
    dot.append("    node [shape = circle];")

    for state in sm.states:
        for transition in state.transitions:
            dot.append(f'    {transition.source.id} -> {transition.target.id} [label="{transition.event}"];')

    dot.append("}")
    return "\n".join(dot)

def sm_to_text(sm) -> str:
    summary = ["# State Machine Summary\n"]
    
    # States section
    summary.append("## States\n")
    for state in sm.states:
        summary.append(f"- {state.id} (initial: {state.initial})\n")
    
    # Transitions section
    summary.append("\n## Transitions\n")
    summary.append("| Source State       | Target State       | Event                        |")
    summary.append("|--------------------|--------------------|------------------------------|")
    for state in sm.states:
        for transition in state.transitions:
            summary.append(f"| {transition.source.id} | {transition.target.id} | {transition.event} |")
    
    # DOT representation section
    summary.append("\n## Chart overview\n")
    summary.append("```dot\n")
    summary.append("digraph G {\n")
    summary.append("    rankdir=LR;\n")
    summary.append("    node [shape = circle];\n")
    for state in sm.states:
        for transition in state.transitions:
            summary.append(f"    {transition.source.id} -> {transition.target.id} [label=\"{transition.event}\"];\n")
    summary.append("}\n")
    summary.append("```\n")
    
    return "\n".join(summary)


def generate_doc_from_sm(sm):
    summary_text = sm_to_text(sm)

    # Adding references to the PNG images if they exist
    if summary_text:
        os.makedirs(os.path.dirname(OUTPUT_MARKDOWN_FILEPATH), exist_ok=True)
        
        # Add header for the state diagrams section
        summary_text += "\n## State Diagrams\n"

        # Check if the simple chart PNG exists before adding it
        if os.path.exists(OUTPUT_SIMPLE_CHART_FILEPATH + ".png"):
            summary_text += "### Simple State Diagram\n"
            summary_text += f"![Simple State Diagram]({OUTPUT_SIMPLE_CHART_FILEPATH}.png)\n\n"
        else:
            summary_text += "*Simple state diagram PNG not generated.*\n\n"

        # Check if the detailed chart PNG exists before adding it
        if os.path.exists(OUTPUT_DETAILED_CHART_FILEPATH):
            summary_text += "### Detailed State Diagram\n"
            summary_text += f"![Detailed State Diagram]({OUTPUT_DETAILED_CHART_FILEPATH})\n\n"
        else:
            summary_text += "*Detailed state diagram PNG not generated.*\n\n"

        # Write the Markdown file
        with open(OUTPUT_MARKDOWN_FILEPATH, "w") as f:
            f.write(summary_text)
            print(f"Markdown file generated as {OUTPUT_MARKDOWN_FILEPATH}")

def generate_simple_png_from_sm(sm):
    dot_format = generate_dot_format(sm)
    # Render the DOT format to a PNG image using Graphviz
    dot = graphviz.Source(dot_format)
    os.makedirs(os.path.dirname(OUTPUT_DIR), exist_ok=True)
    dot.render(OUTPUT_SIMPLE_CHART_FILEPATH, format='png', cleanup=True)

    print(f"State machine simple diagram generated as {OUTPUT_SIMPLE_CHART_FILEPATH}.png")

def generate_detailed_png_from_sm(sm):
    graph = sm._graph()

    # Set graph-wide attributes
    graph.set_rankdir("LR")
    graph.set_nodesep(1.0)
    graph.set_ranksep(1.5)
    
    # Set node attributes
    for node in graph.get_nodes():
        node.set_shape("box")
        node.set_fontsize(10)
        node.set_width(1.5)
    
    # Adjust initial node (start of chart, black circle)
    graph.get_nodes()[0].set_shape("circle")
    graph.get_nodes()[0].set_width(0.25)
    
    # Set edge attributes
    for edge in graph.get_edges():
        edge.set_fontsize(8)
        edge.set_labeldistance(2.0)
        edge.set_labelfontsize(8)
    
    # Generate and save the PNG file
    graph.write_png(OUTPUT_DETAILED_CHART_FILEPATH)
    print(f"State machine detailed diagram generated as {OUTPUT_DETAILED_CHART_FILEPATH}")

def generate_sm_docs_and_graph():
    sm = DeviceRuntimeStateMachine("cognit/test/config/cognit_v2_wrong_user.yml")
    
    # Generate simple chart png
    generate_simple_png_from_sm(sm)
    
    # Generate detailed chart png
    generate_detailed_png_from_sm(sm)
    
    # Generate markdown doc
    generate_doc_from_sm(sm)
    print("\nALL OK")

if __name__ == "__main__":
    generate_sm_docs_and_graph()
