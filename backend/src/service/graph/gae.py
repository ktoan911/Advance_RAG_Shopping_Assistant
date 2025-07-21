import torch
import torch.nn.functional as F

# from graph import Neo4jGraph
from torch_geometric.nn import GCNConv


class GAE(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim, embedding_dim):
        super(GAE, self).__init__()
        self.encoder1 = GCNConv(
            input_dim, hidden_dim
        )  # Initializes a GCN layer: (N, N) -> (N, H)
        self.encoder2 = GCNConv(
            hidden_dim, embedding_dim
        )  # Initializes a GCN layer: (N, H) -> (N, E)

    def encode(self, x, edge_index):
        # x: (N, N), edge_index: (2, M)
        x = F.relu(self.encoder1(x, edge_index))  # (N, N) -> (N, H)
        x = self.encoder2(x, edge_index)  # (N, H) -> (N, E)
        return x  # Node embeddings: (N, E)

    def decode(self, z, edge_index):
        # z: (N, E), edge_index: (2, M)
        src, tgt = edge_index  # src: (M,), tgt: (M,)
        return (z[src] * z[tgt]).sum(dim=1)  # (M, E) -> (M,)

    def forward(self, x, edge_index):
        # x: (N, F_in), edge_index: (2, M)
        z = self.encode(x, edge_index)  # Node embeddings: (N, E)
        reconstructed = self.decode(z, edge_index)  # Reconstruct edges: (M,)
        return z, reconstructed
