// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Hello {
    bool solved = false;

    function solve() public {
        solved = true;
    }

    function isSolved() public view returns (bool) {
        return solved;
    }
}
