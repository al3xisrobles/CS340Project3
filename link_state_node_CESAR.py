from simulator.node import Node
import json


class Link_State_Node(Node):

    def __init__(self, id):
        super().__init__(id)

        # Links of current node with latencies
        self.links = {} # frozenset({}) -> {"source": int,
                        #                   "destination": int,
                        #                   "latency": int,
                        #                   "seq num": int}

        # Full view of graph
        self.graph = {}

    # Return a string
    def __str__(self):
        return f"\nThis is Node {self.id}\nNework: {self.graph}\nMessages: {self.links}"

    def update_graph(self, node1, node2, latency):
        """
        Update self.graph with the new latency between two given nodes
        """

        # If latency is -1, remove the link from the graph
        # (i.e. remove each node from each other's list of neighbors)
        if latency == -1:
            self.graph[node1].pop(node2, None)
            self.graph[node2].pop(node1, None)

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

        #
        link = frozenset((self.id, neighbor))

        # check if its a new link
        if link in self.links:
            seq = self.links[link]["seq num"]
        else:
            seq = -1
            for _, latest_msg in self.links.items():
                self.send_to_neighbor(neighbor, json.dumps(latest_msg))

        message = {
            "source": self.id,
            "destination": neighbor,
            "latency": latency,
            "seq num": seq + 1
        }
        self.links[link] = message
        self.send_to_neighbors(json.dumps(message))

    def process_incoming_routing_message(self, m):
        message = json.loads(m)
        link = frozenset((message["source"], message["destination"]))
        received_sqn = message["seq num"]
        latest_link = self.links.get(link)

        # if link is not known
        if not latest_link:
            self.links[link] = message
            self.update_graph(message["source"], message["destination"],
                              message["latency"])
            self.send_to_neighbors(m)

        else:
            # if it's a new seq number
            if received_sqn > latest_link["seq num"]:
                self.links[link] = message
                self.update_graph(message["source"], message["destination"],
                                  message["latency"])
                self.send_to_neighbors(m)
            # if it's an old seq number
            elif received_sqn < latest_link["seq num"]:
                self.send_to_neighbors(json.dumps(self.links[link]))

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):

        # implement Dijkstra's algorithm
        def dijkstra():
            graph = self.graph

            # Initialize the distance to each node to infinity and the distance to the starting node to 0
            dist = {node: float('inf') for node in graph}
            dist[self.id] = 0

            # Keep track of the visited nodes and the predecessor of each node in the shortest path
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

        shortest_path = dijkstra()
        return shortest_path[1] if shortest_path else -1
