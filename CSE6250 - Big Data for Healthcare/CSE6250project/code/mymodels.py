import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence
from torch.nn.utils.rnn import pad_packed_sequence
from helper import getoutputsize
from helper import getoutputsize2D


class MyCNN(nn.Module):
    def __init__(self, inputsize, use_dropout=False):
        super(MyCNN, self).__init__()

        self.dropout = nn.Dropout(p=0.2)
        self.use_dropout = False
        if use_dropout:
            self.use_dropout = True

        # nextsize is used after the 3rd pooling layer
        # use the getoutputsize function to get the size after each step
        # so it correctly reflects the size at the 3rd pooling layer
        self.nextsize = inputsize
        self.nextsize = getoutputsize(self.nextsize, 5, 1)  # output conv1
        self.nextsize = getoutputsize(self.nextsize, 2, 2)  # output pool1
        self.nextsize = getoutputsize(self.nextsize, 5, 1)  # output conv2
        self.nextsize = getoutputsize(self.nextsize, 2, 2)  # output pool2
        self.nextsize = getoutputsize(self.nextsize, 5, 1)  # output conv3
        self.nextsize = getoutputsize(self.nextsize, 2, 2)  # output pool3

        self.conv1 = nn.Conv1d(
            in_channels=1, out_channels=6, kernel_size=5, stride=1)

        self.conv2 = nn.Conv1d(
            in_channels=6, out_channels=16, kernel_size=5, stride=1)

        self.conv3 = nn.Conv1d(
            in_channels=16, out_channels=16, kernel_size=5, stride=1)

        # default value for stride is kernel_size
        self.pool = nn.MaxPool1d(kernel_size=2, stride=2)

        self.fc1 = nn.Linear(in_features=self.nextsize * 16, out_features=128)
        self.fc2 = nn.Linear(in_features=128, out_features=128)
        self.fc3 = nn.Linear(in_features=128, out_features=5)

    def forward(self, x):
        x = self.conv1(x)  # start with 199 -> 6, f = 5 => (199-5)/1 + 1 => 195
        x = self.pool(torch.relu(x))  # stride 2, f = 2 => (195-2)/2 + 1 => 97
        x = self.conv2(x)  # 97 -> 16, f = 5 => (97-5)/1 + 1 => 93
        x = self.pool(torch.relu(x))  # stride 2, f = 2 => (93-2)/2 + 1 => 46
        x = self.conv3(x)  # 46 -> 16, f = 5 => (46-5)/1 + 1 => 42
        x = self.pool(torch.relu(x))  # stride 2, f = 2 => (42-2)/2 + 1 => 21
        x = x.view(-1, self.nextsize * 16)
        x = torch.relu(self.fc1(x))
        if self.use_dropout:
            x = self.dropout(x)
        x = self.fc2(x)
        x = torch.relu(x)
        if self.use_dropout:
            x = self.dropout(x)
        x = self.fc3(x)
        return x


class MyCNN2D(nn.Module):
    def __init__(self, inputsize):
        super(MyCNN2D, self).__init__()
        # nextsize is used after the 3rd pooling layer
        # use the getoutputsize function to get the size after each step
        # so it correctly reflects the size at the 3rd pooling layer
        self.nextsize = inputsize
        self.nextsize = getoutputsize2D(self.nextsize, 5, 1)  # output conv1
        self.nextsize = getoutputsize2D(self.nextsize, 2, 2)  # output pool1
        self.nextsize = getoutputsize2D(self.nextsize, 5, 1)  # output conv2
        self.nextsize = getoutputsize2D(self.nextsize, 2, 2)  # output pool2
        self.nextsize = getoutputsize2D(self.nextsize, 5, 1)  # output conv3
        self.nextsize = getoutputsize2D(self.nextsize, 2, 2)  # output pool3

        self.conv1 = nn.Conv2d(
            in_channels=3, out_channels=6, kernel_size=5, stride=1)

        self.conv2 = nn.Conv2d(
            in_channels=6, out_channels=16, kernel_size=5, stride=1)

        self.conv3 = nn.Conv2d(
            in_channels=16, out_channels=16, kernel_size=5, stride=1)

        # default value for stride is kernel_size
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        self.fc1 = nn.Linear(
            in_features=self.nextsize[0] * self.nextsize[1] * 16,
            out_features=128)
        self.fc2 = nn.Linear(in_features=128, out_features=128)
        self.fc3 = nn.Linear(in_features=128, out_features=5)

    def forward(self, x):
        x = self.conv1(x)
        x = self.pool(torch.relu(x))
        x = self.conv2(x)
        x = self.pool(torch.relu(x))
        x = self.conv3(x)
        x = self.pool(torch.relu(x))
        x = x.view(-1, self.nextsize[0] * self.nextsize[1] * 16)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        x = torch.relu(x)
        x = self.fc3(x)
        return x
