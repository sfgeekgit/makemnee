const hre = require("hardhat");

async function main() {
  // Contract addresses from deployment
  const MNEE_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
  const BOUNTY_BOARD_ADDRESS = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512";

  // Get signers
  const [creator, hunter] = await hre.ethers.getSigners();

  console.log("\n🎯 Testing BountyBoard Flow\n");
  console.log("Creator address:", creator.address);
  console.log("Hunter address:", hunter.address);

  // Get contract instances
  const mnee = await hre.ethers.getContractAt("MockMNEE", MNEE_ADDRESS);
  const bountyBoard = await hre.ethers.getContractAt("BountyBoard", BOUNTY_BOARD_ADDRESS);

  // Step 1: Check creator's MNEE balance
  console.log("\n📊 Step 1: Check MNEE Balance");
  let balance = await mnee.balanceOf(creator.address);
  console.log(`Creator MNEE balance: ${hre.ethers.formatEther(balance)} MNEE`);

  // Step 2: Approve BountyBoard to spend MNEE
  console.log("\n✅ Step 2: Approve BountyBoard to spend MNEE");
  const bountyAmount = hre.ethers.parseEther("100");
  const approveTx = await mnee.connect(creator).approve(BOUNTY_BOARD_ADDRESS, bountyAmount);
  await approveTx.wait();
  console.log(`Approved ${hre.ethers.formatEther(bountyAmount)} MNEE for BountyBoard`);

  // Step 3: Create a bounty
  console.log("\n🎁 Step 3: Create Bounty");
  const createTx = await bountyBoard.connect(creator).createBounty(bountyAmount);
  const receipt = await createTx.wait();

  // Extract bounty ID from event
  const event = receipt.logs.find(log => {
    try {
      return bountyBoard.interface.parseLog(log).name === "BountyCreated";
    } catch (e) {
      return false;
    }
  });
  const bountyId = bountyBoard.interface.parseLog(event).args.id;

  console.log(`Bounty created with ID: ${bountyId}`);
  console.log(`Bounty amount: ${hre.ethers.formatEther(bountyAmount)} MNEE`);

  // Step 4: Check bounty details
  console.log("\n🔍 Step 4: Query Bounty Details");
  const bounty = await bountyBoard.getBounty(bountyId);
  console.log(`Creator: ${bounty.creator}`);
  console.log(`Amount: ${hre.ethers.formatEther(bounty.amount)} MNEE`);
  console.log(`Status: ${bounty.status === 0n ? "Open" : bounty.status === 1n ? "Completed" : "Cancelled"}`);

  // Step 5: Check balances before release
  console.log("\n💰 Step 5: Balances Before Release");
  const creatorBalance = await mnee.balanceOf(creator.address);
  const hunterBalanceBefore = await mnee.balanceOf(hunter.address);
  const contractBalance = await mnee.balanceOf(BOUNTY_BOARD_ADDRESS);
  console.log(`Creator MNEE: ${hre.ethers.formatEther(creatorBalance)} MNEE`);
  console.log(`Hunter MNEE: ${hre.ethers.formatEther(hunterBalanceBefore)} MNEE`);
  console.log(`Contract MNEE: ${hre.ethers.formatEther(contractBalance)} MNEE`);

  // Step 6: Release bounty to hunter
  console.log("\n🚀 Step 6: Release Bounty to Hunter");
  const releaseTx = await bountyBoard.connect(creator).releaseBounty(bountyId, hunter.address);
  await releaseTx.wait();
  console.log("Bounty released!");

  // Step 7: Check balances after release
  console.log("\n💰 Step 7: Balances After Release");
  const hunterBalanceAfter = await mnee.balanceOf(hunter.address);
  const contractBalanceAfter = await mnee.balanceOf(BOUNTY_BOARD_ADDRESS);
  console.log(`Hunter MNEE: ${hre.ethers.formatEther(hunterBalanceAfter)} MNEE`);
  console.log(`Contract MNEE: ${hre.ethers.formatEther(contractBalanceAfter)} MNEE`);
  console.log(`Hunter received: ${hre.ethers.formatEther(hunterBalanceAfter - hunterBalanceBefore)} MNEE ✅`);

  // Step 8: Check bounty status is now Completed
  console.log("\n🔍 Step 8: Final Bounty Status");
  const finalBounty = await bountyBoard.getBounty(bountyId);
  console.log(`Status: ${finalBounty.status === 0n ? "Open" : finalBounty.status === 1n ? "Completed" : "Cancelled"}`);

  console.log("\n✅ End-to-End Test Complete!\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
