from scripts.helpful_scripts import get_account


from scripts.helpful_scripts import get_account
from brownie import network, config, interface
from scripts.get_weth import get_weth
from web3 import Web3

amount = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    # need to interact with Aave borrow contract, so we need
    # 1. ABI
    # 2. Address
    lending_pool = get_lending_pool()
    print(f"The lending pool address is: {lending_pool}")
    # Approve sending our ERC20 tokens
    approve_erc20(amount, lending_pool.address, erc20_address, account)
    print("Depositing...")
    tx = lending_pool.deposit(
        erc20_address, amount, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("Deposited!")
    # How much to borrow? => pull some off-chain data about our finances
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    print("Let's borrow!")
    # Need a conversion rate i.e. DAI in terms of ETH
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    print(f"We are going to borrow: {amount_dai_to_borrow} DAI")
    # Now we will borrow
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print("We borrowed some DAI!")
    get_borrowable_data(lending_pool, account)
    repay_all(amount, lending_pool, account)


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)
    print("Repaid!")
    print(
        "You just deposited, borrowed, and repayed with Aave, Brownie, and Chainlink!"
    )


def get_asset_price(price_feed_address):
    # ABI
    # Address
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"The DAI/ETH latest price is {converted_latest_price}")
    return float(converted_latest_price)


def get_borrowable_data(lending_pool, account):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    health_factor = Web3.fromWei(health_factor, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} worth of ETH borrowed.")
    print(f"You can borrow {available_borrow_eth} worth of ETH.")
    return (float(available_borrow_eth), float(total_debt_eth))


def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERC20 token...")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)  # 1 block confirmation
    print("Approved!")
    return tx
    # ABI
    # Address


def get_lending_pool():
    # different ways to interact with Aave so sometimes the contract address can change. Using Aave V2 as it is the most popular on mainnet

    lending_ppol_address_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_ppol_address_provider.getLendingPool()
    # ABI
    # Address - have address from above lines of code
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
