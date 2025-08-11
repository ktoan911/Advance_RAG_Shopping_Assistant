import torch
import torch.nn.functional as F
from src.service.graph.gae import GAE

# from graph import Neo4jGraph
from src.service.graph.graph import Neo4jGraph

from src.common.logger import get_logger

logger = get_logger("TRAINING GCN")


def train_gcn(epochs=500, lr=0.01, hidden_dim=16, embedding_dim=8):
    train_data, val_data, features = Neo4jGraph().get_data_matrix_training(training=0.8)
    print(train_data.x)
    print(train_data.edge_index)
    # Initialize the model
    input_dim = features.size(1)
    model = GAE(input_dim, hidden_dim, embedding_dim)

    # Define optimizer and loss function
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    def loss_function(reconstructed, edge_index):
        # Binary cross-entropy loss for adjacency reconstruction
        # Một tensor toàn giá trị 1 với chiều dài bằng số lượng edges (M) trong đồ thị.
        target = torch.ones(edge_index.size(1))  # All edges exist
        # Sự khác biệt giữa logits dự đoán (reconstructed) và các giá trị thực (target).
        return F.binary_cross_entropy_with_logits(reconstructed, target)

    # Train the model and validate after each epoch
    model.train()
    min_val_loss = float("inf")
    for epoch in range(epochs):
        # Training phase
        optimizer.zero_grad()
        embeddings, reconstructed = model(train_data.x, train_data.edge_index)
        train_loss = loss_function(reconstructed, train_data.edge_index)
        train_loss.backward()
        optimizer.step()

        # Validation phase
        model.eval()
        with torch.no_grad():
            val_embeddings, val_reconstructed = model(val_data.x, val_data.edge_index)
            val_loss = loss_function(val_reconstructed, val_data.edge_index)

        if val_loss < min_val_loss:
            min_val_loss = val_loss
            # Save the model if validation loss improves
            torch.save(model.state_dict(), "best_gcn_model.pt")
            logger.info(
                f"Model saved at epoch {epoch + 1} with validation loss: {val_loss.item()}"
            )

        # Switch back to train mode for next epoch
        model.train()

        # Print losses
        logger.info(
            f"Epoch {epoch + 1}, Train Loss: {train_loss.item()}, Validation Loss: {val_loss.item()}"
        )
