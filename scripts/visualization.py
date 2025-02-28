import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
#os.environ... used to hide initial pygame console welcome message
import pygame
from pygame.rect import Rect
# PyGame ⬆

import math
import networkx as nx
# networkX ⬆

from dijkstra import re
from dijkstra import Graph
# functions from dijkstra header ⬆

import pygame_gui
from pygame_gui.windows.ui_file_dialog import UIFileDialog

# UI elements and file systems ⬆

class Object:
    def __init__(self, x, y, name, type='node', radius=None, center=None, weight=None):
        self.radius = radius
        self.center_x, self.center_y = center if center else (x, y)
        self.type = type
        self.name = name
        self.x = x
        self.y = y
        self.weight = weight  # Used for edge weights


class Arrow(Object):
    def __init__(self, start_node, end_node, weight, start_pos, end_pos, name="", color=(255, 255, 255)):
        super().__init__(x=(start_pos[0] + end_pos[0]) / 2, y=(start_pos[1] + end_pos[1]) / 2, name=name, type='edge',
                         weight=weight)
        self.start_node = start_node
        self.color = color
        self.end_node = end_node
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.arrow_size = 15  # Length of the arrowhead
        self.shaft_length = math.sqrt(
            (end_pos[0] - start_pos[0]) ** 2 + (end_pos[1] - start_pos[1]) ** 2) - self.arrow_size

    def render(self, surface, font, background_color, color):
        # Calculate the angle between the nodes
        angle = math.atan2(self.end_pos[1] - self.start_pos[1], self.end_pos[0] - self.start_pos[0])

        # Calculate positions for arrow start and end
        arrow_start_x = self.start_pos[0] + 13 * math.cos(
            angle)  # Move 13 pixels (scaled node radius) outward from the center of start node
        arrow_start_y = self.start_pos[1] + 13 * math.sin(angle)
        arrow_end_x = self.end_pos[0] - 13 * math.cos(
            angle)  # Move 13 pixels (scaled node radius) inward from the center of end node
        arrow_end_y = self.end_pos[1] - 13 * math.sin(angle)

        # Draw the arrow shaft (line) from the adjusted start position to the adjusted end position
        pygame.draw.line(surface, (color), (arrow_start_x, arrow_start_y), (arrow_end_x, arrow_end_y), 2)

        # Draw the arrowhead (triangle) pointing towards the end node
        arrow_x1 = arrow_end_x - self.arrow_size * math.cos(angle - math.pi / 6)
        arrow_y1 = arrow_end_y - self.arrow_size * math.sin(angle - math.pi / 6)
        arrow_x2 = arrow_end_x - self.arrow_size * math.cos(angle + math.pi / 6)
        arrow_y2 = arrow_end_y - self.arrow_size * math.sin(angle + math.pi / 6)

        pygame.draw.polygon(surface, color,
                            [(arrow_end_x, arrow_end_y), (arrow_x1, arrow_y1), (arrow_x2, arrow_y2)])

        # Render and rotate the text to match the angle of the arrow
        # Position the rotated text at the end of the arrow
        edge_weight_font = pygame.font.SysFont("serif", 12)

        text = edge_weight_font.render(f"{self.weight}", False, (0, 221, 242))

        mid_x, mid_y = (arrow_start_x + arrow_end_x) / 2, (arrow_start_y + arrow_end_y) / 2
        surface.blit(text,
                     ((mid_x + 5) - text.get_width() / 2, (mid_y + 5) - text.get_height() / 2))


# Function to reParse the DOT graph input in order to visualize the graph
def parseInput(input_string):
    edges = []
    # Regular expression to match lines in the format: A -- B [weight=3]
    pattern = r'(\w+)\s--\s(\w+)\s\[weight=([0-9.]+)\]'

    # Iterate through each line in the input string
    for match in re.finditer(pattern, input_string):
        nodeA = match.group(1)
        nodeB = match.group(2)
        edgeWeight = float(match.group(3))
        edges.append((nodeA, nodeB, edgeWeight))  # Store as a tuple

    return edges


def renderGraph(graph, surface, font, screen, distances, source_node, opacity=255):
    nodes = set()
    edges = []

    # Use NetworkX to calculate node positions (X, Y)
    nx_graph = nx.DiGraph()  # Directed graph
    for from_node, to_node, weight in graph:
        nx_graph.add_edge(from_node, to_node, weight=weight)

    # Use a NetworkX layout (spring layout in this case)
    node_positions = nx.spectral_layout(nx_graph)

    global SCALE_DIV_X,SCALE_DIV_Y = 2.7, 2.2

    center_x, center_y = surface.get_width() / SCALE_DIV_X, surface.get_height() / SCALE_DIV_Y

    # Scale the node positions (optional, to fit in Pygame window)
    global SCALE_FACTOR = 300  # Scale factor to adjust the layout to the Pygame window size
    node_positions = {node: (pos[0] * SCALE_FACTOR + center_x, pos[1] * SCALE_FACTOR + center_y)
                      for node, pos in node_positions.items()}

    global PROGRAMMERS_PI = 3
    # Determine the size of the circle (based on the number of nodes)
    radius = min(surface.get_width(), surface.get_height()) / PROGRAMMERS_PI
    center_x, center_y = surface.get_width() / scale_div_x, surface.get_height() / PROGRAMMERS_PI

    # Collect unique nodes and edges
    for A, B, weight in graph:
        if A is not B:  # Due to the existence of nodes without outgoing edges we need to check in order not to render its edges and to add it twice
            nodes.add(A)
            nodes.add(B)
            edges.append((A, B, weight))

    # Create node objects
    node_objects = {
        node: Object(
            x=node_positions[node][0],
            y=node_positions[node][1],
            name=node,
            type='node',
            radius=13,
        )
        for node in nodes
    }

    # Create edge (arrow) objects
    arrow_objects = [
        Arrow(
            start_node=nodeA,
            end_node=nodeB,
            weight=weight,
            start_pos=node_positions[nodeA],
            end_pos=node_positions[nodeB],
            name=f"{nodeA}-{nodeB}"
        )
        for nodeA, nodeB, weight in edges
    ]

    def renderNode(node_obj):
        x, y = node_obj.x, node_obj.y
        node_radius = node_obj.radius
        global SCALE_MULTIPLIER = 1.3

        scaled_radius = int(node_radius * SCALE_MULTIPLIER)  # Scale up by 30%
        pygame.draw.circle(surface, (136, 149, 141, opacity), (int(x), int(y)), scaled_radius)
        # Render node ID
        NodeID = font.render(f"{node_obj.name}", False, 0x606d5d)

        global X_DIV,Y_DIV = 2.4, 2.2
        screen.blit(NodeID, (x - scaled_radius / X_DIV, y - scaled_radius / Y_DIV))
        # Render text (distance or label)

    # Render all nodes and edges
    for node_obj in node_objects.values():
        renderNode(node_obj)
    for arrow_obj in arrow_objects:
        arrow_obj.render(surface, font, opacity, color=(255, 255, 255))

    return node_objects, arrow_objects


def render_table(distances, nodes, surface, font, screen, table_background_color, table_border_color):
    # Define margins for spacing within the table
    margin = 1
    num_rows = len(nodes)
    num_cols = 2  # One column for node name and one for its distance or value
    cell_width = screen.get_width() // 20  # Adjust the width of the table
    cell_height = screen.get_height() // (num_rows + 1)  # Adjust the height based on the number of nodes

    # Define position to place the table in the upper-right corner
    table_x = screen.get_width() - (cell_width * num_cols) - margin  # Right-aligned
    table_y = margin  # Top-aligned

    # Loop through each node and draw the table cells
    row = 0  # Row index to go through each node
    for node_name, node_obj in sorted(nodes.items()):
        for col in range(num_cols):
            x = table_x + col * cell_width
            y = table_y + row * cell_height

            # Draw the cell background (white)
            pygame.draw.rect(surface, table_background_color,
                             (x + margin, y + margin, cell_width - 2 * margin, cell_height - 2 * margin))
            # Draw the cell border (black)
            pygame.draw.rect(surface, table_border_color,
                             (x + margin, y + margin, cell_width - 2 * margin, cell_height - 2 * margin), 2)

            # Render the node name in the first column
            if col == 0:
                value = node_name  # Use the node name
            else:
                # Use the distance or '∞' if the distance is not available
                value = f"{distances.get(node_name, '\N{INFINITY}')}"

            # Render the value in the cell
            text = font.render(value, False, (0, 0, 0))  # Black color for text
            text_rect = text.get_rect(center=(x + cell_width // 2, y + cell_height // 2))
            surface.blit(text, text_rect)

        row += 1  # Move to the next row


def render_shortest_path(data, graph, source, target, background_color, screen, font, distances):
    # Get the shortest path
    shortest_path_nodes = graph.shortest_path(source, target)

    if not shortest_path_nodes or len(shortest_path_nodes) == 1:
        #Return 0 if there is no path
        return 0

    # Construct edges for the shortest path
    shortest_path_edges = [
        (shortest_path_nodes[i], shortest_path_nodes[i + 1])
        for i in range(len(shortest_path_nodes) - 1)
    ]

    # Render the full graph, dimmed (no weights visible)
    nodes, arrows = renderGraph(data, screen, font, screen, distances, source, opacity=0)

    # Dim the entire graph
    for arrow in arrows:
        arrow.render(screen, font, background_color, color=(128, 128, 128, 128))

    for node in nodes.values():
        pygame.draw.circle(screen, (100, 100, 100), (int(node.x), int(node.y)), node.radius)

    # Highlight the shortest path edges
    for edge in shortest_path_edges:
        nodeA, nodeB = edge

        # Find the corresponding arrow object
        for arrow in arrows:
            if arrow.start_node == nodeA and arrow.end_node == nodeB:
                arrow.render(screen, font, background_color, color=(255, 0, 0))  # Red for shortest path
                break

    # Highlight the shortest path nodes
    for node_name in shortest_path_nodes:
        node = nodes[node_name]
        pygame.draw.circle(screen, (0, 255, 0), (int(node.x), int(node.y)), node.radius)

        # Render node labels
        label = font.render(node.name, False, (255, 0, 0))
        xOffset = 10
        programmers_pi = 3

        screen.blit(label, (node.x + xOffset - node.radius, node.y + xOffset - node.radius * (programmers_pi/2)))

    return 1

# Function to create a Pygame_GUI button
def create_gui_button(manager, text, x, y, width, height):
    return pygame_gui.elements.UIButton(
        relative_rect=Rect((x, y), (width, height)),
        text=text,
        manager=manager,
    )


def visualize(graph, source_node, target_node,select_source, select_target):
    pygame.init()
    screen = pygame.display.set_mode((1200, 800), pygame.SRCALPHA)
    _clock = pygame.time.Clock()

    # Snapshot management
    current_snapshot_index = 0

    sourceSelect, targetSelect = select_source, select_target
    nodesForSelection = []
    manager = pygame_gui.UIManager((1200, 800))

    title = "Visualization of Dijkstra's algorithm"
    pygame.display.set_caption(title)

    data = parseInput(graph)
    font = pygame.font.SysFont("Arial", 14, italic=True)

    # Initialize the graph and add edges
    g = Graph()
    for nodeA, nodeB, weight in data:
        g.add_edge(nodeA, nodeB, weight)
        if nodeA not in nodesForSelection:
            nodesForSelection.append(nodeA)
        elif nodeB not in nodesForSelection:
            nodesForSelection.append(nodeB)


    # Get distances using the Dijkstra algorithm
    distances, _, steps = g.dijkstra(source_node, target_node)
    screenWidth, screenHeight = screen.get_width(), screen.get_height()
    #region UI_INIT

    buttonPrev = create_gui_button(manager=manager, x=100, y=screenHeight - 60, width=100, height=40,
                                   text="Previous Step")

    buttonNext = create_gui_button(manager=manager, x=screenWidth - 150, y=screenHeight - 60, width=100,
                                   height=40, text="Next Step")

    buttonSP = create_gui_button(manager=manager, x=10, y=10, width=100, height=40,
                                 text="Shortest Path")

    buttonLoadGraph = create_gui_button(manager=manager, x=10, y=60, width=100, height=40,
                                        text="Load Graph")

    #Dropdown menus to select source and target nodes and their respective labels
    sourceDropdown = pygame_gui.elements.UIDropDownMenu(nodesForSelection, sourceSelect, (10, 110, 50, 40), manager=manager)
    sourceLabel = pygame_gui.elements.UILabel(
        relative_rect=Rect((60,110), (100, 40)),
        text="Source Node",
        manager=manager,
    )
    targetDropdown = pygame_gui.elements.UIDropDownMenu(nodesForSelection, targetSelect,(10, 160, 50, 40), manager=manager)
    targetLabel = pygame_gui.elements.UILabel(
        relative_rect=Rect((60, 160), (100, 40)),
        text="Target Node",
        manager=manager,
    )

    currentIndexLabel = pygame_gui.elements.UILabel(
        relative_rect=Rect(screen.get_width() / 2.3 - 15, screen.get_height() - 64, 200, 40),
        manager=manager,
        text=f"current step: {current_snapshot_index}"
        )

    # Create a panel for the overlay
    overlay_panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect((350, 250), (300, 120)),
        manager=manager,
        object_id="#overlay_panel"
    )

    # Create a label for the message on the overlay panel
    message_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((40, -20), (220, 100)),
        text=f"No path from node {sourceSelect} to node {targetSelect}",
        manager=manager,
        container=overlay_panel
    )

    # Create a label for the message on the overlay panel
    continue_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((40, 30), (220, 50)),
        text=f"Press any key to continue",
        manager=manager,
        container=overlay_panel
    )

    #endregion


    # Initially hide the overlay panel
    overlay_panel.hide()
    overlay_panel_on = False


    #Function which renders the data in the upcoming step into the table
    def render_snapshot():
        if current_snapshot_index < len(steps):
            # Get the current step
            current_distances = steps[current_snapshot_index]
            # Update table values to reflect the current distances
            render_table(current_distances, nodes, screen, font, screen, 0xDDF2EB, 0x606d5d)


    file_dialog = None
    renderSP = False
    second = 1000.0
    #region Main_Loop
    # Event loop for visualization
    while True:
        time_delta = _clock.tick(60) / second
        screen.fill(0x606d5d)
        for event in pygame.event.get():
            manager.process_events(event)
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    raise SystemExit(0)

            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN and overlay_panel_on:
                    overlay_panel.hide()
                    renderSP = False
                    select_source = "A"
                    visualize(graph, source_node, target_node, select_source, select_target)

            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                # Previous button
                if event.ui_element == buttonPrev:
                    if renderSP:
                        renderSP = False
                        overlay_panel.hide()

                    if current_snapshot_index != 0:
                        current_snapshot_index -= 1
                        currentIndexLabel.set_text(text=f"current step: {current_snapshot_index}")
                        render_snapshot()
                        print("previous button clicked")
                        buttonNext.enable()

                    if current_snapshot_index == 0:
                        print("no more previous events")
                        buttonPrev.disable()


                # Next button
                if event.ui_element == buttonNext:
                    if current_snapshot_index < len(steps):
                        current_snapshot_index += 1
                        currentIndexLabel.set_text(text=f"current step: {current_snapshot_index}")
                        render_snapshot()
                        buttonPrev.enable()
                        print("next button clicked")

                    if current_snapshot_index == len(steps) - 1:
                        print("no more upcoming events")
                        renderSP = not renderSP
                        buttonNext.disable()





                # Shortest path button
                if event.ui_element == buttonSP:
                    print("Shortest path button clicked")
                    renderSP = not renderSP

                # File Dialog button
                if event.ui_element == buttonLoadGraph:
                    print("Load Graph button clicked!")
                    if file_dialog is None:
                        file_dialog = UIFileDialog(
                            rect=pygame.Rect(100, 100, 600, 400),
                            manager=manager,
                            window_title="Load a Graph File",
                        )

            #Logic which handles selecting source and target from the available nodes
            if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                if event.ui_element == sourceDropdown:
                    visualize(graph, f"{event.text}", f"{targetSelect}", f"{event.text}",
                              f"{targetSelect}")
                if event.ui_element == targetDropdown:
                    visualize(graph, f"{sourceSelect}", f"{event.text}", f"{sourceSelect}",
                              f"{event.text}")

            if event.type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:
                if file_dialog is not None and event.ui_element == file_dialog:
                    print(f"File selected: {event.text}")
                    try:
                        with open(event.text, "r") as graph_file:
                            graph_DOT = graph_file.read()
                        # Call the visualization function
                        visualize(graph_DOT, f"{sourceSelect}", f"{targetSelect}", sourceSelect, targetSelect)
                    except Exception as e:
                        print(f"Node {e} doesn't exist in submitted graph!")
                    file_dialog = None  # Close the dialog after the selection

        # Render the graph
        nodes, arrows = renderGraph(data, screen, font, screen, distances, source_node)

        # Render default step of the algorithm
        render_snapshot()

        # Render pygame_GUI
        manager.update(time_delta)
        manager.draw_ui(screen)

        # Check whether to render the Shortest path
        if renderSP:
            if render_shortest_path(data, g, source_node, target_node, 0x606d5d, screen, font, distances) == 0:
                overlay_panel.show()
                overlay_panel_on = True



        #Core pygame functions for rendering anything
        pygame.display.flip()
        pygame.display.update()
        _clock.tick(60)
    #endregion
