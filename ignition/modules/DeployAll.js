const { buildModule } = require("@nomicfoundation/hardhat-ignition/modules");

module.exports = buildModule("DeployAll", (m) => {
  // Deploy MockMNEE first
  const mnee = m.contract("MockMNEE");

  // Deploy BountyBoard with MockMNEE address
  const bountyBoard = m.contract("BountyBoard", [mnee]);

  return { mnee, bountyBoard };
});
