from simulator.node import Node
import json


class Link_State_Node(Node):
    def __init__(self, id):

        # Node ID
        super().__init__(id)

        # Graph
        self.graph = {}

        # Links
        self.links = {}

    def __str__(self):
        """
        Return a string with the current node's ID, graph, and links
        """
        return f"Node {self.id}: {json.dumps(self.graph, indent=4)}"

    # update graph
        # If latency is -1, remove the link from the graph
        # (i.e. remove each node from each other's list of neighbors)
            # Try to remove
        # If latency is not -1, latency is being updated and not deleted
            # If each node is in self.graph
                # Add each node to graph with given latency for other node

    def link_has_been_updated(self, neighbor, latency):
        """
        Simulation has updated a link incident on a node
        """

        # Update the graph with the given neighbor and latency
        # Create a link as a frozenset between itself and its neighbor

        # If it's not a new link
            # Set the current sequence number to the one the node knows from self.links
        # Otherwise, if the link is new
            # Send current node's links to new neighbor to properly update the new neighbor with the latest sequence numbers for the links
            # Make sequence number to 0 to start

        # Create message according to instructions
        # Add the message to self.links for the current link
        # Send the message to all its neighbors

        pass

    # Fill in this function
    def process_incoming_routing_message(self, m):
        """
        Called by simulator when a node passes a message along to a new node
        """

        # Parse JSON message
        # Create link between source and destination as frozenset DS
        # Parse the sequence number
        # Parse the source node
        # Find the link in self.links

        # If link is not known
            # Add the message as a new link in self.links
            # Update the graph
            # Pass the message along to the node's neighbors
        # Otherwise, if the link is known
            # Check if it's a new seq number
                # Add the message as a new link in self.links
                # Update the graph
                # Pass the message along to the node's neighbors
            # Otherwise, if it's an old seq number (i.e. simulation bug)
                # Send the newer message back to the node who sent the older message

        pass

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        """
        Get the next hop by implementing Dijkstra's algorithm
        on the node's current graph
        """
        pass
