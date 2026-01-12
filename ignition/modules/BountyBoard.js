const { buildModule } = require("@nomicfoundation/hardhat-ignition/modules");

module.exports = buildModule("BountyBoard", (m) => {
  const mneeAddress = m.getParameter("mneeAddress");
  const bountyBoard = m.contract("BountyBoard", [mneeAddress]);
  return { bountyBoard };
});
