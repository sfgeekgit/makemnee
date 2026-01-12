require("@nomicfoundation/hardhat-ethers");
require("@nomicfoundation/hardhat-chai-matchers");
require("@nomicfoundation/hardhat-network-helpers");
require("@nomicfoundation/hardhat-ignition-ethers");

// Load custom tasks
require("./tasks/mint");

module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },

  networks: {
    // Local Hardhat network (default)
    hardhat: {
      // No config needed - works out of the box
    },

    // Sepolia testnet
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || "",
      accounts: process.env.SEPOLIA_PRIVATE_KEY ? [process.env.SEPOLIA_PRIVATE_KEY] : [],
      chainId: 11155111
    },

    // Ethereum mainnet (future use)
    mainnet: {
      url: process.env.MAINNET_RPC_URL || "",
      accounts: process.env.MAINNET_PRIVATE_KEY ? [process.env.MAINNET_PRIVATE_KEY] : [],
      chainId: 1
    }
  },

  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  }
};
