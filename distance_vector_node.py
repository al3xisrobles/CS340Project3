from simulator.node import Node
import json

# Each DV node must compute:
# - Its own DV using 1 & 2.  This will be optimal, given the info I have.
# - Whenever either 1 or 2 changes, I must recompute my DV.
# - Whenever my DV changes, send my updated DV to all neighbors.

class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)

        # Each DV node must store:
        # 1. Its outbound links (who do they connect to, and at what cost?)
        self.outbound_links = {}

        # 2. Each neighbor’s latest DV (who can I reach through neighbors?)
        self.neighbors_dv = {}

        # 3. Its own distance vector (DV) to each destination
        self.dv = {}

        # Each DV should include the full routing path for each destination
        # (AS_PATH in BGP)

    # Return a string
    def __str__(self):
        return f"Node {self.id}: outbound_links={self.outbound_links}, neighbors_dv={self.neighbors_dv}"

    # When the link costs change, update its DV and notify neighbors
    def link_has_been_updated(self, neighbor, latency):
        """
        # 1. Node detects local link cost change
        # 2. Recalculates distance vector
        # 3. If DV changed, notify neighbors (in JSON format, with timestamp)
        """
        # latency = -1 if delete a link
        if latency == -1:
            del self.outbound_links[neighbor]
            del self.neighbors_dv[neighbor]
        else:
            self.outbound_links[neighbor] = latency
            self.neighbors_dv[neighbor] = {n: c for n, c in self.outbound_links.items() if n != neighbor}

        dv_changed = self._recalculate_dv()

        if dv_changed:
            self._send_dv_to_neighbors()

    # You must record the new information within the node, and (depending on
    # the message contents) you may need to send messages to neighbors.
    def process_incoming_routing_message(self, m):
        message = json.loads(m)
        sender_id = message["sender_id"]
        dv = message["dv"]
        self.neighbors_dv[sender_id] = dv

        dv_changed = self._recalculate_dv()

        if dv_changed:
            self._send_dv_to_neighbors()

    def get_next_hop(self, destination):
        """
        Returns the next hop to reach the given destination based on the node's
        current knowledge. If no path to the destination is found, -1 is returned.
        """
        if destination == self.id:
            return self.id
        next_hop = -1
        min_cost = float("inf")
        for neighbor, dv in self.neighbors_dv.items():
            if destination in dv and dv[destination] < min_cost:
                next_hop = neighbor
                min_cost = dv[destination]
        return next_hop

    # Recompute this node's distance vector and return True if it has changed
    def _recalculate_dv(self):
        """
        Recomputes the node's distance vector based on its outbound links and
        its neighbors' latest distance vectors. Returns True if the node's
        distance vector has changed, False otherwise.
        """
        new_dv = {self.id: (0, [self.id])}
        for neighbor, link_info in self.outbound_links.items():

            if not isinstance(link_info, tuple):
                # Handle the case where link_info is not a tuple
                continue
            latency, _ = link_info

            for dest, (prev_latency, prev_path) in self.neighbors_dv[neighbor].items():
                dest_latency = latency + prev_latency
                dest_path = prev_path + [self.id]
                if dest not in new_dv or dest_latency < new_dv[dest][0]:
                    new_dv[dest] = (dest_latency, dest_path)

        if new_dv != self.dv:
            self.dv = new_dv
            return True
        return False

    # Send DV to all neighbors
    def _send_dv_to_neighbors(self):
        dv = json.dumps({"from": self.id,
                         "vector": self.dv[self.id],
                         "timestamp": self.get_time()})
        self.send_to_neighbors(dv)
