const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");

describe("BountyBoard", function () {
  // Fixture: setup state once, reused across tests
  async function deployFixture() {
    const [owner, hunter, creator, anotherUser] = await ethers.getSigners();

    // Deploy MockMNEE
    const MockMNEE = await ethers.getContractFactory("MockMNEE");
    const mnee = await MockMNEE.deploy();

    // Deploy BountyBoard
    const BountyBoard = await ethers.getContractFactory("BountyBoard");
    const bountyBoard = await BountyBoard.deploy(await mnee.getAddress());

    // Give creator some MNEE tokens
    const amount = ethers.parseEther("1000");
    await mnee.mint(creator.address, amount);

    return { bountyBoard, mnee, owner, hunter, creator, anotherUser };
  }

  describe("Deployment", function () {
    it("Should deploy successfully", async function () {
      const { bountyBoard } = await loadFixture(deployFixture);
      expect(await bountyBoard.getAddress()).to.be.properAddress;
    });

    it("Should set MNEE token address correctly", async function () {
      const { bountyBoard, mnee } = await loadFixture(deployFixture);
      expect(await bountyBoard.mnee()).to.equal(await mnee.getAddress());
    });
  });

  describe("createBounty", function () {
    it("Should create bounty and lock MNEE", async function () {
      const { bountyBoard, mnee, creator } = await loadFixture(deployFixture);

      const amount = ethers.parseEther("100");
      await mnee.connect(creator).approve(await bountyBoard.getAddress(), amount);

      const creatorBalanceBefore = await mnee.balanceOf(creator.address);
      const contractBalanceBefore = await mnee.balanceOf(await bountyBoard.getAddress());

      await bountyBoard.connect(creator).createBounty(amount);

      const creatorBalanceAfter = await mnee.balanceOf(creator.address);
      const contractBalanceAfter = await mnee.balanceOf(await bountyBoard.getAddress());

      expect(creatorBalanceAfter).to.equal(creatorBalanceBefore - amount);
      expect(contractBalanceAfter).to.equal(contractBalanceBefore + amount);
    });

    it("Should return a unique bounty ID", async function () {
      const { bountyBoard, mnee, creator } = await loadFixture(deployFixture);

      const amount = ethers.parseEther("100");
      await mnee.connect(creator).approve(await bountyBoard.getAddress(), amount * 2n);

      const tx1 = await bountyBoard.connect(creator).createBounty(amount);
      const receipt1 = await tx1.wait();
      const event1 = receipt1.logs.find(log => {
        try {
          return bountyBoard.interface.parseLog(log).name === "BountyCreated";
        } catch (e) {
          return false;
        }
      });
      const bountyId1 = bountyBoard.interface.parseLog(event1).args.id;

      const tx2 = await bountyBoard.connect(creator).createBounty(amount);
      const receipt2 = await tx2.wait();
      const event2 = receipt2.logs.find(log => {
        try {
          return bountyBoard.interface.parseLog(log).name === "BountyCreated";
        } catch (e) {
          return false;
        }
      });
      const bountyId2 = bountyBoard.interface.parseLog(event2).args.id;

      expect(bountyId1).to.not.equal(bountyId2);
    });

    it("Should emit BountyCreated event", async function () {
      const { bountyBoard, mnee, creator } = await loadFixture(deployFixture);

      const amount = ethers.parseEther("100");
      await mnee.connect(creator).approve(await bountyBoard.getAddress(), amount);

      await expect(bountyBoard.connect(creator).createBounty(amount))
        .to.emit(bountyBoard, "BountyCreated");
    });

    it("Should fail if amount is 0", async function () {
      const { bountyBoard, creator } = await loadFixture(deployFixture);

      await expect(
        bountyBoard.connect(creator).createBounty(0)
      ).to.be.revertedWith("Amount must be > 0");
    });

    it("Should fail if user hasn't approved MNEE transfer", async function () {
      const { bountyBoard, creator } = await loadFixture(deployFixture);

      const amount = ethers.parseEther("100");

      await expect(
        bountyBoard.connect(creator).createBounty(amount)
      ).to.be.reverted;
    });

    it("Should fail if user has insufficient MNEE balance", async function () {
      const { bountyBoard, mnee, anotherUser } = await loadFixture(deployFixture);

      const amount = ethers.parseEther("100");
      await mnee.connect(anotherUser).approve(await bountyBoard.getAddress(), amount);

      await expect(
        bountyBoard.connect(anotherUser).createBounty(amount)
      ).to.be.reverted;
    });
  });

  describe("releaseBounty", function () {
    async function createBountyFixture() {
      const fixture = await deployFixture();
      const { bountyBoard, mnee, creator } = fixture;

      const amount = ethers.parseEther("100");
      await mnee.connect(creator).approve(await bountyBoard.getAddress(), amount);

      const tx = await bountyBoard.connect(creator).createBounty(amount);
      const receipt = await tx.wait();
      const event = receipt.logs.find(log => {
        try {
          return bountyBoard.interface.parseLog(log).name === "BountyCreated";
        } catch (e) {
          return false;
        }
      });
      const bountyId = bountyBoard.interface.parseLog(event).args.id;

      return { ...fixture, bountyId, bountyAmount: amount };
    }

    it("Should release MNEE to hunter address", async function () {
      const { bountyBoard, mnee, creator, hunter, bountyId, bountyAmount } =
        await loadFixture(createBountyFixture);

      const hunterBalanceBefore = await mnee.balanceOf(hunter.address);

      await bountyBoard.connect(creator).releaseBounty(bountyId, hunter.address);

      const hunterBalanceAfter = await mnee.balanceOf(hunter.address);
      expect(hunterBalanceAfter).to.equal(hunterBalanceBefore + bountyAmount);
    });

    it("Should update bounty status to Completed", async function () {
      const { bountyBoard, creator, hunter, bountyId } =
        await loadFixture(createBountyFixture);

      await bountyBoard.connect(creator).releaseBounty(bountyId, hunter.address);

      const bounty = await bountyBoard.getBounty(bountyId);
      expect(bounty.status).to.equal(1); // Status.Completed = 1
    });

    it("Should emit BountyCompleted event", async function () {
      const { bountyBoard, creator, hunter, bountyId, bountyAmount } =
        await loadFixture(createBountyFixture);

      await expect(bountyBoard.connect(creator).releaseBounty(bountyId, hunter.address))
        .to.emit(bountyBoard, "BountyCompleted")
        .withArgs(bountyId, hunter.address, bountyAmount);
    });

    it("Should fail if caller is not creator", async function () {
      const { bountyBoard, anotherUser, hunter, bountyId } =
        await loadFixture(createBountyFixture);

      await expect(
        bountyBoard.connect(anotherUser).releaseBounty(bountyId, hunter.address)
      ).to.be.revertedWith("Only creator can release");
    });

    it("Should fail if bounty is not Open status", async function () {
      const { bountyBoard, creator, hunter, bountyId } =
        await loadFixture(createBountyFixture);

      // Release once
      await bountyBoard.connect(creator).releaseBounty(bountyId, hunter.address);

      // Try to release again
      await expect(
        bountyBoard.connect(creator).releaseBounty(bountyId, hunter.address)
      ).to.be.revertedWith("Bounty not open");
    });

    it("Should fail if hunter address is zero address", async function () {
      const { bountyBoard, creator, bountyId } =
        await loadFixture(createBountyFixture);

      await expect(
        bountyBoard.connect(creator).releaseBounty(bountyId, ethers.ZeroAddress)
      ).to.be.revertedWith("Invalid hunter address");
    });
  });

  describe("cancelBounty", function () {
    async function createBountyFixture() {
      const fixture = await deployFixture();
      const { bountyBoard, mnee, creator } = fixture;

      const amount = ethers.parseEther("100");
      await mnee.connect(creator).approve(await bountyBoard.getAddress(), amount);

      const tx = await bountyBoard.connect(creator).createBounty(amount);
      const receipt = await tx.wait();
      const event = receipt.logs.find(log => {
        try {
          return bountyBoard.interface.parseLog(log).name === "BountyCreated";
        } catch (e) {
          return false;
        }
      });
      const bountyId = bountyBoard.interface.parseLog(event).args.id;

      return { ...fixture, bountyId, bountyAmount: amount };
    }

    it("Should refund MNEE to creator", async function () {
      const { bountyBoard, mnee, creator, bountyId, bountyAmount } =
        await loadFixture(createBountyFixture);

      const creatorBalanceBefore = await mnee.balanceOf(creator.address);

      await bountyBoard.connect(creator).cancelBounty(bountyId);

      const creatorBalanceAfter = await mnee.balanceOf(creator.address);
      expect(creatorBalanceAfter).to.equal(creatorBalanceBefore + bountyAmount);
    });

    it("Should update bounty status to Cancelled", async function () {
      const { bountyBoard, creator, bountyId } =
        await loadFixture(createBountyFixture);

      await bountyBoard.connect(creator).cancelBounty(bountyId);

      const bounty = await bountyBoard.getBounty(bountyId);
      expect(bounty.status).to.equal(2); // Status.Cancelled = 2
    });

    it("Should emit BountyCancelled event", async function () {
      const { bountyBoard, creator, bountyId } =
        await loadFixture(createBountyFixture);

      await expect(bountyBoard.connect(creator).cancelBounty(bountyId))
        .to.emit(bountyBoard, "BountyCancelled")
        .withArgs(bountyId);
    });

    it("Should fail if caller is not creator", async function () {
      const { bountyBoard, anotherUser, bountyId } =
        await loadFixture(createBountyFixture);

      await expect(
        bountyBoard.connect(anotherUser).cancelBounty(bountyId)
      ).to.be.revertedWith("Only creator can cancel");
    });

    it("Should fail if bounty is not Open status", async function () {
      const { bountyBoard, creator, bountyId } =
        await loadFixture(createBountyFixture);

      // Cancel once
      await bountyBoard.connect(creator).cancelBounty(bountyId);

      // Try to cancel again
      await expect(
        bountyBoard.connect(creator).cancelBounty(bountyId)
      ).to.be.revertedWith("Can only cancel open bounties");
    });
  });

  describe("getBounty", function () {
    it("Should return correct bounty details for Open bounty", async function () {
      const { bountyBoard, mnee, creator } = await loadFixture(deployFixture);

      const amount = ethers.parseEther("100");
      await mnee.connect(creator).approve(await bountyBoard.getAddress(), amount);

      const tx = await bountyBoard.connect(creator).createBounty(amount);
      const receipt = await tx.wait();
      const event = receipt.logs.find(log => {
        try {
          return bountyBoard.interface.parseLog(log).name === "BountyCreated";
        } catch (e) {
          return false;
        }
      });
      const bountyId = bountyBoard.interface.parseLog(event).args.id;

      const bounty = await bountyBoard.getBounty(bountyId);
      expect(bounty.creator).to.equal(creator.address);
      expect(bounty.amount).to.equal(amount);
      expect(bounty.status).to.equal(0); // Status.Open = 0
    });

    it("Should return correct status for Completed bounty", async function () {
      const { bountyBoard, mnee, creator, hunter } = await loadFixture(deployFixture);

      const amount = ethers.parseEther("100");
      await mnee.connect(creator).approve(await bountyBoard.getAddress(), amount);

      const tx = await bountyBoard.connect(creator).createBounty(amount);
      const receipt = await tx.wait();
      const event = receipt.logs.find(log => {
        try {
          return bountyBoard.interface.parseLog(log).name === "BountyCreated";
        } catch (e) {
          return false;
        }
      });
      const bountyId = bountyBoard.interface.parseLog(event).args.id;

      await bountyBoard.connect(creator).releaseBounty(bountyId, hunter.address);

      const bounty = await bountyBoard.getBounty(bountyId);
      expect(bounty.status).to.equal(1); // Status.Completed = 1
    });

    it("Should return correct status for Cancelled bounty", async function () {
      const { bountyBoard, mnee, creator } = await loadFixture(deployFixture);

      const amount = ethers.parseEther("100");
      await mnee.connect(creator).approve(await bountyBoard.getAddress(), amount);

      const tx = await bountyBoard.connect(creator).createBounty(amount);
      const receipt = await tx.wait();
      const event = receipt.logs.find(log => {
        try {
          return bountyBoard.interface.parseLog(log).name === "BountyCreated";
        } catch (e) {
          return false;
        }
      });
      const bountyId = bountyBoard.interface.parseLog(event).args.id;

      await bountyBoard.connect(creator).cancelBounty(bountyId);

      const bounty = await bountyBoard.getBounty(bountyId);
      expect(bounty.status).to.equal(2); // Status.Cancelled = 2
    });
  });

  describe("Edge Cases", function () {
    it("Should allow multiple bounties to be created", async function () {
      const { bountyBoard, mnee, creator } = await loadFixture(deployFixture);

      const amount = ethers.parseEther("100");
      await mnee.connect(creator).approve(await bountyBoard.getAddress(), amount * 3n);

      await bountyBoard.connect(creator).createBounty(amount);
      await bountyBoard.connect(creator).createBounty(amount);
      await bountyBoard.connect(creator).createBounty(amount);

      // If we get here, all three bounties were created successfully
      expect(true).to.be.true;
    });

    it("Should generate unique IDs for each bounty", async function () {
      const { bountyBoard, mnee, creator } = await loadFixture(deployFixture);

      const amount = ethers.parseEther("100");
      await mnee.connect(creator).approve(await bountyBoard.getAddress(), amount * 2n);

      const tx1 = await bountyBoard.connect(creator).createBounty(amount);
      const receipt1 = await tx1.wait();
      const event1 = receipt1.logs.find(log => {
        try {
          return bountyBoard.interface.parseLog(log).name === "BountyCreated";
        } catch (e) {
          return false;
        }
      });
      const bountyId1 = bountyBoard.interface.parseLog(event1).args.id;

      const tx2 = await bountyBoard.connect(creator).createBounty(amount);
      const receipt2 = await tx2.wait();
      const event2 = receipt2.logs.find(log => {
        try {
          return bountyBoard.interface.parseLog(log).name === "BountyCreated";
        } catch (e) {
          return false;
        }
      });
      const bountyId2 = bountyBoard.interface.parseLog(event2).args.id;

      expect(bountyId1).to.not.equal(bountyId2);
    });

    it("Should not allow releasing same bounty twice", async function () {
      const { bountyBoard, mnee, creator, hunter } = await loadFixture(deployFixture);

      const amount = ethers.parseEther("100");
      await mnee.connect(creator).approve(await bountyBoard.getAddress(), amount);

      const tx = await bountyBoard.connect(creator).createBounty(amount);
      const receipt = await tx.wait();
      const event = receipt.logs.find(log => {
        try {
          return bountyBoard.interface.parseLog(log).name === "BountyCreated";
        } catch (e) {
          return false;
        }
      });
      const bountyId = bountyBoard.interface.parseLog(event).args.id;

      await bountyBoard.connect(creator).releaseBounty(bountyId, hunter.address);

      await expect(
        bountyBoard.connect(creator).releaseBounty(bountyId, hunter.address)
      ).to.be.revertedWith("Bounty not open");
    });

    it("Should not allow cancelling same bounty twice", async function () {
      const { bountyBoard, mnee, creator } = await loadFixture(deployFixture);

      const amount = ethers.parseEther("100");
      await mnee.connect(creator).approve(await bountyBoard.getAddress(), amount);

      const tx = await bountyBoard.connect(creator).createBounty(amount);
      const receipt = await tx.wait();
      const event = receipt.logs.find(log => {
        try {
          return bountyBoard.interface.parseLog(log).name === "BountyCreated";
        } catch (e) {
          return false;
        }
      });
      const bountyId = bountyBoard.interface.parseLog(event).args.id;

      await bountyBoard.connect(creator).cancelBounty(bountyId);

      await expect(
        bountyBoard.connect(creator).cancelBounty(bountyId)
      ).to.be.revertedWith("Can only cancel open bounties");
    });

    it("Should allow different users to create bounties independently", async function () {
      const { bountyBoard, mnee, creator, anotherUser } = await loadFixture(deployFixture);

      // Give anotherUser some MNEE
      const amount = ethers.parseEther("100");
      await mnee.mint(anotherUser.address, amount);

      // Both users create bounties
      await mnee.connect(creator).approve(await bountyBoard.getAddress(), amount);
      await mnee.connect(anotherUser).approve(await bountyBoard.getAddress(), amount);

      await bountyBoard.connect(creator).createBounty(amount);
      await bountyBoard.connect(anotherUser).createBounty(amount);

      // If we get here, both bounties were created successfully
      expect(true).to.be.true;
    });
  });
});
