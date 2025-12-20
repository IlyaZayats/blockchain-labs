// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DoubleString {
    // Переменная состояния: здесь хранится текущее значение (удвоенная строка)
    string private value;

    // Событие (лог) для удобства отслеживания изменений
    event ValueChanged(string oldValue, string newValue, address indexed caller);

    /// @notice Возвращает текущее сохранённое значение
    function getValue() external view returns (string memory) {
        return value;
    }

    /// @notice Принимает строку s и сохраняет в state удвоенную строку: s + s
    function setValue(string calldata s) external {
        string memory oldVal = value;
        value = string(abi.encodePacked(s, s));
        emit ValueChanged(oldVal, value, msg.sender);
    }
}