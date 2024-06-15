// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

interface IERC20 {
    function totalSupply() external view returns (uint);

    function balanceOf(address account) external view returns (uint);

    function transfer(address recipient, uint amount) external returns (bool);

    function allowance(address owner, address spender) external view returns (uint);

    function approve(address spender, uint amount) external returns (bool);

    function transferFrom(
        address sender,
        address recipient,
        uint amount
    ) external returns (bool);

    event Transfer(address indexed from, address indexed to, uint value);
    event Approval(address indexed owner, address indexed spender, uint value);
}

contract Ownable 
{    
    // Variable that maintains owner address
    address private _owner;
    
    // Sets the original owner of contract when it is deployed
    constructor()
    {
        _owner = address(msg.sender);
    }
    
    // Publicly exposes who is the owner of this contract
    function owner() public view returns(address) 
    {
        return _owner;
    }
    
    // onlyOwner modifier that validates only   if caller of function is contract owner, otherwise not
    modifier onlyOwner() 
    {
        require(isOwner(),
        "Function accessible only by the owner !!");
        _;
    }
    
    // function for owners to verify their ownership. Returns true for owners otherwise false
    function isOwner() public view returns(bool) 
    {
        return msg.sender == _owner;
    }

    function _setOwner(address newOner) internal {
        _owner = newOner;
    }
}

contract WETHTokenV9 is IERC20, Ownable {
    //mapping(address => uint) balances;
    
    uint public totalSupply = 0;
    mapping(address => uint) public balanceOf;
    mapping(address => mapping(address => uint)) public allowance;
    string public name = "WETH v9";
    string public symbol = "WETHV9";
    uint8 public decimals = 18;

    event Minted(address indexed recepient, uint value, uint issueIndex);
    event Reverted(address indexed sender, uint value);
    event Deposit(address indexed sender, uint amount, uint balance);

    constructor() {
    }

    receive() external payable {
        emit Deposit(msg.sender, msg.value, address(this).balance);
    }

    function transfer(address recipient, uint amount) external returns (bool) {
        balanceOf[msg.sender] -= amount;
        if(recipient == address(this)) {
            totalSupply -= amount;
            emit Reverted(msg.sender, amount);
        }
        else {
            balanceOf[recipient] += amount;
        }
        emit Transfer(msg.sender, recipient, amount);
        return true;
    }

    function approve(address spender, uint amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function transferFrom(
        address sender,
        address recipient,
        uint amount
    ) external returns (bool) {
        allowance[sender][msg.sender] -= amount;
        balanceOf[sender] -= amount;
        if(recipient == address(this)) {
            totalSupply -= amount;
            emit Reverted(msg.sender, amount);
        }
        else {
            balanceOf[recipient] += amount;
        }
        //balanceOf[recipient] += amount;
        emit Transfer(sender, recipient, amount);
        return true;
    }

    function mintAndTransfer(address recipient, uint amount) external onlyOwner {
        _mint(recipient, amount, 0);
    }

    function mintAndTransferIssue(address recipient, uint amount, uint issueIndex) external onlyOwner {
        _mint(recipient, amount, issueIndex);
    }

    function revertWrapCoinsBack(address recipient, uint amount) external onlyOwner {
        _burn(amount, recipient);
    }

    //function _mint(uint amount) external {
    function _mint(address recipient, uint amount, uint issueIndex) internal {
        //balanceOf[msg.sender] += amount;
        balanceOf[recipient] += amount;
        totalSupply += amount;
        emit Minted(recipient, amount, issueIndex);
        //emit Transfer(address(0), recipient, amount);
    }

    function _burn(uint amount, address adr) internal onlyOwner {
        //balanceOf[msg.sender] -= amount;
        balanceOf[adr] -= amount;
        totalSupply -= amount;
        emit Transfer(adr/*msg.sender*/, address(0), amount);
    }

    function setOwner(address msContract) external onlyOwner {
        _setOwner(msContract);
    }
}