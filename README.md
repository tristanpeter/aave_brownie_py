1. Swap our ETH for WETH
2. Deposit some ETH (WETH) into AAVE
3. Borrow some asset with the ETH collateral
    1> Sell that borrowed asset. (Short selling)
4. Repay everything back.

Testing:
    Default Testing Network => Development with Mocking
    If no oracles being used => Mainnet-fork

Integration test: Kovan
Unit tests: Mainnet-fork (not deploying any mocks).