// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

interface WrapCoinIface{
    function mintAndTransferIssue(address recipient, uint amount, uint issueIndex) external;
    function revertWrapCoinsBack(address recipient, uint amount) external;
}

contract MSIssuerV6 {
    event Deposit(address indexed sender, uint amount, uint balance);
    event SubmitTransaction(
        address indexed owner,
        uint indexed txIndex,
        address indexed to,
        uint value,
        bytes data
    );
    event ConfirmTransaction(address indexed owner, uint indexed txIndex);
    event RevokeConfirmation(address indexed owner, uint indexed txIndex);
    event ExecuteTransaction(address indexed owner, uint indexed txIndex);

    event IssueInited(
        address indexed owner,
        uint indexed issueIndex,
        address indexed to,
        uint value
    );
    event IssueSigned(address indexed owner, uint indexed issueIndex);
    //event RevokeSign(address indexed owner, uint indexed issueIndex);
    event IssueProvided(address indexed owner, uint indexed issueIndex);

    address public provider;
    address[] public guardians;
    mapping(address => bool) public isGuardian;
    uint public numConfirmationsRequired;
    uint public numSignsRequired;
    uint public issueRewardPercent = 5;
    uint public signersRewardPercent = 4;

    struct Transaction {
        address to;
        uint value;
        bytes data;
        bool executed;
        uint numConfirmations;
    }

    struct Issue {
        address to;
        uint value;
        uint signersReward;
        bool provided;
        uint numSigns;
    }

    address public constant WrappedTokenAddress = address(0xfa9CaD4Ab2BC505e805986fC27e1c6A44853E2CD);

    // mapping from tx index => owner => bool
    mapping(uint => mapping(address => bool)) public isConfirmed;

    // mapping from issue index => owner => bool
    mapping(uint => mapping(address => bool)) public isSigned;

    Transaction[] public transactions;

    Issue[] public issues;

    modifier onlyOwner() {
        require(isGuardian[msg.sender], "not guardian");
        _;
    }

    modifier onlyGuardian() {
        require(isGuardian[msg.sender], "not guardian");
        _;
    }

    modifier onlyProvider() {
         require(msg.sender == provider, "not provider");
        _;
    }

    modifier txExists(uint _txIndex) {
        require(_txIndex < transactions.length, "tx does not exist");
        _;
    }

    modifier issueExists(uint _issueIndex) {
        require(_issueIndex < issues.length, "issue does not exist");
        _;
    }

    modifier notExecuted(uint _txIndex) {
        require(!transactions[_txIndex].executed, "tx already executed");
        _;
    }

    modifier notProvided(uint _issueIndex) {
        require(!issues[_issueIndex].provided, "issue already provided");
        _;
    }

    modifier notConfirmed(uint _txIndex) {
        require(!isConfirmed[_txIndex][msg.sender], "tx already confirmed");
        _;
    }

    modifier notSigned(uint _issueIndex) {
        require(!isSigned[_issueIndex][msg.sender], "issue already signed");
        _;
    }

    constructor(address[] memory _guardians, uint _numConfirmationsRequired, uint _numSignsRequired) {
        require(_guardians.length > 0, "guardians required");
        require(
            _numConfirmationsRequired > 0 &&
                _numConfirmationsRequired <= _guardians.length,
            "invalid number of required confirmations"
        );
        require(
            _numSignsRequired > 0 &&
                _numSignsRequired <= _guardians.length,
            "invalid number of required signs"
        );

        for (uint i = 0; i < _guardians.length; i++) {
            address guardian = _guardians[i];

            require(guardian != address(0), "invalid guardian");
            require(!isGuardian[guardian], "guardian not unique");

            isGuardian[guardian] = true;
            guardians.push(guardian);
        }

        provider = msg.sender;
        numConfirmationsRequired = _numConfirmationsRequired;
        numSignsRequired = _numSignsRequired;
    }

    receive() external payable {
        emit Deposit(msg.sender, msg.value, address(this).balance);
    }

    function submitTransaction(
        address _to,
        uint _value,
        bytes memory _data
    ) public onlyOwner {
        uint txIndex = transactions.length;

        transactions.push(
            Transaction({
                to: _to,
                value: _value,
                data: _data,
                executed: false,
                numConfirmations: 0
            })
        );

        emit SubmitTransaction(msg.sender, txIndex, _to, _value, _data);
    }

    function initIssue(address _to, uint _value) public onlyProvider {
        // Generate the issueId.
        //issueId = bytes20(keccak256(_to, block.blockhash(block.number - 1)));
        uint issueIndex = issues.length;

        // Reward the validator for signing a transaction
        //uint issueRewardAmount = (_value * issueRewardPercent) / 100;
        uint issueRewardAmount = 1000000000000000;
        payable(msg.sender).transfer(issueRewardAmount);

        //uint m_signersRewardAmount = ((_value-issueRewardAmount) * signersRewardPercent ) / 100;
        uint m_signersRewardAmount = 2000000000000000;
        uint toAdrValue = (_value-issueRewardAmount-m_signersRewardAmount);

        issues.push(
            Issue({
                to: _to,
                value: toAdrValue,
                signersReward: m_signersRewardAmount,
                provided: false,
                numSigns: 0
            })
        );

        emit IssueInited(msg.sender, issueIndex, _to, toAdrValue);
    }

    function confirmTransaction(
        uint _txIndex
    ) public onlyOwner txExists(_txIndex) notExecuted(_txIndex) notConfirmed(_txIndex) {
        Transaction storage transaction = transactions[_txIndex];
        transaction.numConfirmations += 1;
        isConfirmed[_txIndex][msg.sender] = true;

        emit ConfirmTransaction(msg.sender, _txIndex);
    }

    function signIssue(uint _issueIndex) public onlyGuardian
    issueExists(_issueIndex) notProvided(_issueIndex) notSigned(_issueIndex) {
        Issue storage issue = issues[_issueIndex];
        issue.numSigns += 1;
        isSigned[_issueIndex][msg.sender] = true;

        emit IssueSigned(msg.sender, _issueIndex);
    }

    function executeTransaction(
        uint _txIndex
    ) public onlyOwner txExists(_txIndex) notExecuted(_txIndex) {
        Transaction storage transaction = transactions[_txIndex];

        require(
            transaction.numConfirmations >= numConfirmationsRequired,
            "cannot execute tx"
        );

        transaction.executed = true;

        (bool success, ) = transaction.to.call{value: transaction.value}(
            transaction.data
        );
        require(success, "tx failed");

        emit ExecuteTransaction(msg.sender, _txIndex);
    }

    function provideIssue(uint _issueIndex) public onlyProvider issueExists(_issueIndex) notProvided(_issueIndex) {
        Issue storage issue = issues[_issueIndex];
        require(issue.numSigns >= numSignsRequired, "cannot provide issue");

        uint needToPay = numSignsRequired;
        for(uint i = 0; ((i < guardians.length) && (needToPay != 0)); i++)
        {
            address g_adr = guardians[i];
            if(isSigned[_issueIndex][g_adr] == true) {
                payable(g_adr).transfer(issue.signersReward/numSignsRequired);
                needToPay -= 1;
            }
        }

        issue.provided = true;
        emit IssueProvided(msg.sender, _issueIndex);
    }

    // this function calls than Issue in SberNet is provided
    function callMintWETH(address _to, uint _value, uint issueIndex) public onlyProvider {
        // todo: also add signs from guardians
        WrapCoinIface WETHSTokenContract = WrapCoinIface(WrappedTokenAddress);
        WETHSTokenContract.mintAndTransferIssue(_to, _value, issueIndex);
    }

    function revokeConfirmation(
        uint _txIndex
    ) public onlyOwner txExists(_txIndex) notExecuted(_txIndex) {
        Transaction storage transaction = transactions[_txIndex];

        require(isConfirmed[_txIndex][msg.sender], "tx not confirmed");

        transaction.numConfirmations -= 1;
        isConfirmed[_txIndex][msg.sender] = false;

        emit RevokeConfirmation(msg.sender, _txIndex);
    }

    function getOwners() public view returns (address[] memory) {
        return guardians;
    }

    function getGuardians() public view returns (address[] memory) {
        return guardians;
    }

    function getTransactionCount() public view returns (uint) {
        return transactions.length;
    }

    function getIssuesCount() public view returns (uint) {return issues.length;}

    function getTransaction(
        uint _txIndex
    )
        public
        view
        returns (
            address to,
            uint value,
            bytes memory data,
            bool executed,
            uint numConfirmations
        )
    {
        Transaction storage transaction = transactions[_txIndex];

        return (
            transaction.to,
            transaction.value,
            transaction.data,
            transaction.executed,
            transaction.numConfirmations
        );
    }

    function getIssue(uint _issueIndex) public view returns (
            address to,
            uint value,
            bool provided,
            uint numSigns
        )
    {
        Issue storage issue = issues[_issueIndex];

        return (
            issue.to,
            issue.value,
            issue.provided,
            issue.numSigns
        );
    }
}