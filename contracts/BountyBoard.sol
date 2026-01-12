// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract BountyBoard {
    enum Status { Open, Completed, Cancelled }

    struct Bounty {
        address creator;
        uint256 amount;
        Status status;
    }

    IERC20 public mnee;
    uint256 private nonce;
    mapping(bytes32 => Bounty) public bounties;

    event BountyCreated(bytes32 indexed id, address indexed creator, uint256 amount);
    event BountyCompleted(bytes32 indexed id, address indexed hunter, uint256 amount);
    event BountyCancelled(bytes32 indexed id);

    constructor(address _mnee) {
        mnee = IERC20(_mnee);
    }

    function createBounty(uint256 amount) external returns (bytes32) {
        require(amount > 0, "Amount must be > 0");
        require(mnee.transferFrom(msg.sender, address(this), amount), "Transfer failed");

        bytes32 id = keccak256(abi.encodePacked(block.timestamp, msg.sender, nonce++));

        bounties[id] = Bounty({
            creator: msg.sender,
            amount: amount,
            status: Status.Open
        });

        emit BountyCreated(id, msg.sender, amount);
        return id;
    }

    function releaseBounty(bytes32 id, address hunter) external {
        Bounty storage b = bounties[id];
        require(b.status == Status.Open, "Bounty not open");
        require(b.creator == msg.sender, "Only creator can release");
        require(hunter != address(0), "Invalid hunter address");

        b.status = Status.Completed;
        require(mnee.transfer(hunter, b.amount), "Transfer failed");

        emit BountyCompleted(id, hunter, b.amount);
    }

    function cancelBounty(bytes32 id) external {
        Bounty storage b = bounties[id];
        require(b.creator == msg.sender, "Only creator can cancel");
        require(b.status == Status.Open, "Can only cancel open bounties");

        b.status = Status.Cancelled;
        require(mnee.transfer(b.creator, b.amount), "Transfer failed");

        emit BountyCancelled(id);
    }

    function getBounty(bytes32 id) external view returns (
        address creator,
        uint256 amount,
        Status status
    ) {
        Bounty storage b = bounties[id];
        return (b.creator, b.amount, b.status);
    }
}
