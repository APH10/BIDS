# Copyright (C) 2024 APH10 Limited
# SPDX-License-Identifier: Apache-2.0

class BIDSGraph:

    def __init__(self):
        self.graph={}

    def process(self):
        # Process text section
        # For each function, identify external functions which are used
        #