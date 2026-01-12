const { buildModule } = require("@nomicfoundation/hardhat-ignition/modules");

module.exports = buildModule("MockMNEE", (m) => {
  const mnee = m.contract("MockMNEE");
  return { mnee };
});
