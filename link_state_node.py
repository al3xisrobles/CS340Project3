from simulator.node import Node
import json


class Link_State_Node(Node):

    def __init__(self, id):
        """
        Constructor
        """

        # ID of node
        super().__init__(id)

        # Links of current node with latencies
        self.links = {} # { frozenset({nodeID, nodeID}) -> {"source": nodeID,
                        #                                   "destination": nodeID,
                        #                                   "latency": int,
                        #                                   "seq num": int}, }

        # Full view of graph
        self.graph = {} # { nodeID -> { nodeID -> latency, }, }

    def __str__(self):
        """
        Return a string with the current node's ID, graph, and links
        """
        return f"\nThis is Node {self.id}\nNework: {self.graph}\nMessages: {self.links}"

    def update_graph(self, node1, node2, latency):
        """
        Update self.graph with the new latency between two given nodes
        """

        # If latency is -1, remove the link from the graph
        # (i.e. remove each node from each other's list of neighbors)
        if latency == -1:

            # Try to remove
            try:
                self.graph[node1].pop(node2, None)
                self.graph[node2].pop(node1, None)
            except KeyError as e:
                print('ERROR: ', e)

        # If latency is not -1, latency is being updated and not deleted
        else:

            # If each node is in self.graph
            if node1 not in self.graph:
                # Add each node to graph with given latency for other node
                self.graph[node1] = {}
            if node2 not in self.graph:
                self.graph[node2] = {}
            self.graph[node1][node2] = latency
            self.graph[node2][node1] = latency

    def link_has_been_updated(self, neighbor, latency):
        """
        Simulation has updated a link incident on a node
        """

        # Update the graph with the given neighbor and latency
        self.update_graph(self.id, neighbor, latency)

        # Create a link as a frozenset between itself and its neighbor
        link = frozenset((self.id, neighbor))

        # If it's not a new link
        if link in self.links:

            # Set the current sequence number to the one the node knows from self.links
            seq = self.links[link]["seq num"]

        # Otherwise, if the link is new
        else:

            # Send current node's links to new neighbor to properly update the
            # new neighbor with the latest sequence numbers for the links
            for _, latest_msg in self.links.items():
                self.send_to_neighbor(neighbor, json.dumps(latest_msg))

            # Make sequence number to 0 to start
            seq = -1

        # Create message according to instructions
        message = {
            "source": self.id,
            "destination": neighbor,
            "latency": latency,
            "seq num": seq + 1
        }

        # Add the message to self.links for the current link
        self.links[link] = message

        # Send the message to all its neighbors
        self.send_to_neighbors(json.dumps(message))

    def process_incoming_routing_message(self, m):
        """
        Called by simulator when a node passes a message along to a new node
        """

        # Parse JSON message
        message = json.loads(m)

        # Create link between source and destination as frozenset DS
        link = frozenset((message["source"], message["destination"]))

        # Parse the sequence number
        received_sqn = message["seq num"]

        # Parse the source node
        source_node = message["source"]

        # Find the link in self.links
        latest_link = self.links.get(link)

        # If link is not known
        if not latest_link:

            # Add the message as a new link in self.links
            self.links[link] = message

            # Update the graph
            self.update_graph(message["source"], message["destination"],
                              message["latency"])

            # Pass the message along to the node's neighbors
            self.send_to_neighbors(m)

        # Otherwise, if the link is known
        else:

            # Check if it's a new seq number
            if received_sqn > latest_link["seq num"]:

                # Add the message as a new link in self.links
                self.links[link] = message

                # Update the graph
                self.update_graph(message["source"], message["destination"],
                                  message["latency"])

                # Pass the message along to the node's neighbors
                self.send_to_neighbors(m)

            # Otherwise, if it's an old seq number (i.e. simulation bug)
            elif received_sqn < latest_link["seq num"]:

                # Send the newer message back to the node who sent the older message
                self.send_to_neighbor(source_node, json.dumps(self.links[link]))

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        """
        Get the next hop by implementing Dijkstra's algorithm
        on the node's current graph
        """

        # Implement Dijkstra's algorithm
        def dijkstra():

            # Copy instance graph
            graph = self.graph

            # Initialize the distance to each node to infinity and the
            # distance to the starting node to 0
            dist = {node: float('inf') for node in graph}
            dist[self.id] = 0

            # Keep track of the visited nodes and the predecessor
            # of each node in the shortest path
            visited = set()
            predecessor = {node: None for node in graph}

            # Iterate until we've visited all reachable nodes
            while len(visited) < len(graph):

                # Find the unvisited node with the smallest distance
                curr_node = None
                curr_dist = float('inf')
                for node in graph:
                    if node not in visited and dist[node] < curr_dist:
                        curr_node = node
                        curr_dist = dist[node]

                # If there are no more reachable nodes, we're done
                if curr_node is None:
                    break

                # Mark the current node as visited
                visited.add(curr_node)

                # Update the distances to adjacent nodes
                for adj_node, weight in graph[curr_node].items():
                    new_dist = dist[curr_node] + weight
                    if new_dist < dist[adj_node]:
                        dist[adj_node] = new_dist
                        predecessor[adj_node] = curr_node

            # Build the path from start to end by following the predecessor links
            path = []
            curr_node = destination
            while curr_node is not None:
                path.append(curr_node)
                curr_node = predecessor[curr_node]

            # If we didn't reach the end node, there's no path
            if path[-1] != self.id:
                return []

            # Reverse the path and return it
            path.reverse()
            return path

        # Call Dijkstra's
        shortest_path = dijkstra()

        # If there is a shortest path, return the path
        return shortest_path[1] if shortest_path else -1
