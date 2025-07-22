// SPDX-License-Identifier: MIT
// Fixed version to avoid foundry/4668
pragma solidity 0.8.27;

contract Hello {
    bool solved = false;

    function solve() public {
        solved = true;
    }

    function isSolved() public view returns (bool) {
        return solved;
    }
}
