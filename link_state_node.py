from simulator.node import Node
import json
import heapq


class Link_State_Node(Node):
    def __init__(self, id):

        # Node ID
        super().__init__(id)

        # Graph
        self.graph = {}

        # Links
        self.neighbor_links = {}

    def __str__(self):
        """
        Return a string with the current node's ID, graph, and links
        """
        return f"Node {self.id}: {self.neighbor_links}"

    def update_graph(self, latency, node1, node2):

        # Candidate link
        link = frozenset({node1, node2})

        # If latency is -1, remove the link from the graph
        # (i.e. remove each node from each other's list of neighbors)
        if latency == -1:

            # Try to remove
            try:
                del self.graph[link]
                print(link)
            except:
                pass

        # Latency is not -1, so link will be updated
        else:

            # Add link to graph with given latency for other node
            self.graph[link] = latency


    def link_has_been_updated(self, neighbor, latency):
        """
        Simulation has updated a link incident on a node
        """

        # Update the graph with the given neighbor and latency
        self.update_graph(latency, self.id, neighbor)

        # Create a link as a frozenset between itself and its neighbor
        link = frozenset({self.id, neighbor})

        # If it's not a new link
        if link in self.neighbor_links:

            # Set the current sequence number to the one the node knows from self.neighbor_links
            seq = self.neighbor_links[link]["seq"] + 1

        # Otherwise, if the link is new
        else:

            # Make sequence number to 0 to start
            seq = 0

            # Send current node's links to new neighbor to properly update the
            # new neighbor with the latest sequence numbers for the links
            for link_info in self.neighbor_links.values():
                self.send_to_neighbor(neighbor, json.dumps(link_info))

        # Create message according to instructions
        msg = {"src": self.id,
               "dst": neighbor,
               "lat": latency,
               "seq": seq}

        # Add the message to self.neighbor_links for the current link
        self.neighbor_links[link] = msg

        # Send the message to all its neighbors
        self.send_to_neighbors(json.dumps(msg))

    # Fill in this function
    def process_incoming_routing_message(self, m):
        """
        Called by simulator when a node passes a message along to a new node
        """

        # Parse JSON message
        msg = json.loads(m)

        # Create link between source and destination as frozenset DS
        link = frozenset({msg["src"], msg["dst"]})

        # Parse message info
        seq = msg["seq"]
        src = msg["src"]
        dst = msg["dst"]
        lat = msg["lat"]

        # If link is known
        if link in self.neighbor_links:

            # Check if it's an old seq number (i.e. simulation bug)
            if seq < self.neighbor_links[link]["seq"]:

                # Convert msg back to string with JSON
                msg = json.dumps(msg)

                # Send the newer message back to the node who sent the older message
                self.send_to_neighbor(src, msg)
                return

            else:

                # Do nothing! This is when the equilibrium state can occur
                pass

        # Otherwise, if the link is not known or if it's known but a new seq number
        else:

            # Update self.neighbor_links
            self.neighbor_links[link] = msg

            # Convert msg back to string with JSON
            msg = json.dumps(msg)

            # Update the graph
            self.update_graph(lat, src, dst)

            # Pass the message along to the node's neighbors
            self.send_to_neighbors(msg)

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        """
        Get the next hop by implementing Dijkstra's algorithm
        on the node's current graph
        """

        # Create a list (set) of all nodes in the graph, since the
        # graph is currently made of links as keys
        all_nodes = set()
        for link in self.graph:

            # Parse nodes from link
            node1, node2 = link

            # Add each node to link (without repeats since all_nodes is a set)
            all_nodes.add(node1)
            all_nodes.add(node2)

        # Initialize the distance to each node to infinity
        dist = {node: float('inf') for node in all_nodes}

        # Initialize the distance to the starting node to 0
        dist[self.id] = 0

        # Keep track of the visited nodes and the predecessor of each node in the shortest path
        visited = set()
        predecessor = {node: None for node in all_nodes}

        # Use a heap to keep track of the nodes to visit next
        heap = [(0, self.id)] # heap of (total cost, node ID)
        heapq.heapify(heap)

        # Iterate until we've visited all reachable nodes
        while heap:

            # Pop the node with the smallest distance from the heap
            curr_dist, curr_node = heapq.heappop(heap)

            # If we've already visited this node, continue
            if curr_node in visited:
                continue

            # Mark the current node as visited
            visited.add(curr_node)

            # Update the distances to adjacent nodes
            for link in self.graph:

                # If the current node is on either side of a link
                if curr_node in link:

                    # Get the node's neighbor on the other side of the link
                    neighbor = set(link - set([curr_node])).pop()

                    # Get the latency of the link
                    latency = self.graph[link]

                    # Calculate the new distance to the neighbor
                    new_dist = dist[curr_node] + latency

                    # If the new distance to the neighbor is less than previous
                    if new_dist < dist[neighbor]:

                        # Update the distance to the neighbor
                        dist[neighbor] = new_dist

                        # Update the neighbor's predecesor
                        predecessor[neighbor] = curr_node

                        # Push the neighbor onto the heap
                        heapq.heappush(heap, (new_dist, neighbor))

        # Build the path from start to end by following the predecessor links
        path = []
        curr_node = destination
        while curr_node is not None:
            path.append(curr_node)
            curr_node = predecessor[curr_node]

        # Reverse path so that it goes source -> destination
        path = path[::-1]

        print('Path:', str(path))

        # If we didn't reach the end node, there's no path
        if path[0] != self.id:
            return -1

        # Return the next hop in the path
        next_hop = path[1]
        return next_hop
