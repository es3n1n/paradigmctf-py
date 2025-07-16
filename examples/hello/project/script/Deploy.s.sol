// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import "forge-ctf/CTFDeployer.sol";
import "forge-ctf/CTFChallenge.sol";

import "src/Hello.sol";

contract Deploy is CTFDeployer {
    function deploy(address system, address player) internal override returns (CTFChallenge[] memory challenges) {
        vm.startBroadcast(system);

        Hello hello = new Hello();

        challenges = new CTFChallenge[](1);
        challenges[0] = CTFChallenge("Hello", address(hello));

        vm.stopBroadcast();
    }
}
