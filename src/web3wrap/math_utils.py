import math

Q96 = 2**96

def get_price_from_sqrt_price(sqrt_price_x96):
    return (sqrt_price_x96 / Q96) ** 2

def get_tick_at_sqrt_price(sqrt_price_x96):
    tick = math.floor(math.log((sqrt_price_x96 / Q96)**2) / math.log(1.0001))
    return tick

def get_token_amounts(liquidity, sqrt_price_x96, tick_low, tick_high):
    sqrt_ratio_a = math.sqrt(1.0001 ** tick_low)
    sqrt_ratio_b = math.sqrt(1.0001 ** tick_high)
    current_tick = get_tick_at_sqrt_price(sqrt_price_x96)
    sqrt_price = sqrt_price_x96 / Q96
    amount0 = 0
    amount1 = 0

    if current_tick < tick_low:
        amount0 = math.floor(liquidity * ((sqrt_ratio_b - sqrt_ratio_a) / (sqrt_ratio_a * sqrt_ratio_b)))
    elif current_tick >= tick_high:
        amount1 = math.floor(liquidity * (sqrt_ratio_b - sqrt_ratio_a))
    elif current_tick >= tick_low and current_tick < tick_high:
        amount0 = math.floor(liquidity * ((sqrt_ratio_b - sqrt_price) / (sqrt_price * sqrt_ratio_b)))
        amount1 = math.floor(liquidity * (sqrt_price - sqrt_ratio_a))

    print("Amount Token0 in lowest decimal:", amount0)
    print("Amount Token1 in lowest decimal:", amount1)
    
    return [amount0, amount1]

def nearest_numbers_divisible_by_figure(number, figure: int):
    """
    Function to find the nearest numbers divisible by 60, both above and below the given number.
    Works for both positive and negative numbers.
    """
    nearest_below = number - (number % figure)
    nearest_above = nearest_below + figure

    # Adjust for negative numbers
    if number < 0 and number % figure != 0:
        nearest_below = number - (figure + number % figure)

    return nearest_below, nearest_above


def uniswap_v3_tick_to_price(tick):
    return pow(1.0001, tick)