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
        self.outbound_links = {} # neighbor_id -> cost
        #                   = {4: 2,
        #                      2: 2,
        #                      1: 2}

        # 2. Each neighbor’s latest DV (who can I reach through neighbors?)
        self.neighbors_dv = {} # neighbor_id -> {link -> [cost, AS_PATH]}
        #                 = {4: {3: [2, [3]],
        #                        1: [4, [3, 1]],
        #                        2: [4, [3, 2]]},
        #                    2: {3: [2, [3]],
        #                        1: [2, [1]],
        #                        0: [4, [1, 0]]},
        #                    1: {0: [2, [0]],
        #                        2: [2, [2]],
        #                        3: [2, [3]]}}

        # 3. Its own distance vector (DV) to each destination
        self.dv = {}
        #       = {4: [2, [4]],
        #          2: [2, [2]],
        #          1: [2, [1]]}

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
        # If latency = -1, link is to be deleted
        if latency == -1:

            # Remove neighbor from outgoing_links
            del self.outbound_links[neighbor]

            # Remove neighbor from neighbor_dv
            del self.neighbors_dv[neighbor]

        # Link's cost has been changed
        else:

            # Update cost to neighbor
            self.outbound_links[neighbor] = latency

            # Update neighbor's DV
            new_neighbors_dv = {}
            for neighbor_dv in self.neighbors_dv:
                new_neighbors_dv[neighbor_dv] = self.neighbors_dv[neighbor_dv]
                for n in new_neighbors_dv[neighbor_dv]:
                    if n == neighbor:
                        new_neighbors_dv[neighbor_dv][n][0] = latency
            self.neighbors_dv = new_neighbors_dv

        # Recalcluate DV
        dv_changed = self._recalculate_dv()

        # If node's recalculated DV is changed, send to all neighbors
        if dv_changed:
            self._send_dv_to_neighbors()

    # You must record the new information within the node, and (depending on
    # the message contents) you may need to send messages to neighbors.
    def process_incoming_routing_message(self, m):

        # Message
        message = json.loads(m)

        # Sender ID
        sender_id = message["sender_id"]

        # DV
        dv = message["dv"]

        # ********** FIX *********
        self.neighbors_dv[sender_id] = dv

        # Recalculate DV
        dv_changed = self._recalculate_dv()

        # Send DV to neighbors
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
        dv = json.dumps({"sender_id": self.id,
                         "dv": self.dv,
                         "timestamp": self.get_time()})
        self.send_to_neighbors(dv)
