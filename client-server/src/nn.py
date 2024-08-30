import torch
import torch.nn as nn


class StaticNetwork(nn.Module):
    def __init__(self):
        super(StaticNetwork, self).__init__()
        self.fc1 = nn.Linear(200, 16)  # Input: 10x20 grid, Hidden: 16 neurons
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(16, 7)  # Output: 7 possible moves
        self.softmax = nn.Softmax(dim=1)  # For probability distribution

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.softmax(x)
        return x


def crossover(parent_a, parent_b):
    child = StaticNetwork()
    for child_param, parent_a_param, parent_b_param in zip(
        child.parameters(), parent_a.parameters(), parent_b.parameters()
    ):
        # Coin flip for each weight
        mask = torch.randint(0, 2, parent_a_param.shape).bool()
        child_param.data = torch.where(mask, parent_a_param.data, parent_b_param.data)
    return child


def mutate(network, mutation_rate=0.01):
    for param in network.parameters():
        # Randomly select weights to mutate
        mask = torch.rand(param.shape) < mutation_rate
        # Add small random noise to the selected weights
        param.data += (
            torch.randn(param.shape) * mask * 0.1
        )  # Adjust 0.1 for mutation strength
