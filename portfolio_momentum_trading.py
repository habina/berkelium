"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume
from quantopian.pipeline.factors import EWMA, Latest
from quantopian.pipeline import CustomFactor
import talib
import math
import numpy as np

def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    context.look_back_long = 120
    context.look_back_middle = 60
    context.look_back_short = 15
    
    context.long_leverage = 0.5
    context.short_leverage = -0.5
    
    # current position, 0 stands for empty exposure, 1 stands for full exposure
    context.pos = 0
    
    # Rebalance every day, 1 hour after market open.
    schedule_function(my_rebalance, date_rules.every_day(), time_rules.market_open(hours=6))
     
    # Record tracking variables at the end of each day.
    schedule_function(my_record_vars, date_rules.every_day(), time_rules.market_close())
     
    # Create our dynamic stock selector.
    attach_pipeline(my_pipeline(context), 'my_pipeline')

        
def my_pipeline(context):
    """
    A function to create our dynamic stock selector (pipeline). Documentation on
    pipeline can be found here: https://www.quantopian.com/help#pipeline-title
    """
    pipe = Pipeline()
    
    # span stands for past 120 days, need doulbe window length to get 120 data point.
    ewma120 = EWMA.from_span([USEquityPricing.close], window_length=2 * context.look_back_long, span=context.look_back_long)
    pipe.add(ewma120, "ewma120")
    ewma60 = EWMA.from_span([USEquityPricing.close], window_length=2 * context.look_back_middle, span=context.look_back_middle)
    pipe.add(ewma60, "ewma60")
    ewma15 = EWMA.from_span([USEquityPricing.close], window_length=2 * context.look_back_short, span=context.look_back_short)
    pipe.add(ewma15, "ewma15")
    
    pipe.add(Latest(inputs=[USEquityPricing.close]), "yes_price")

    momentum = (ewma120 - ewma60).abs() + (ewma60 - ewma15).abs()
    
    middle_momentum = momentum.percentile_between(0, 5)
    
    # Create a dollar volume factor.
    dollar_volume = AverageDollarVolume(window_length=1, mask=middle_momentum)
    pipe.add(dollar_volume, 'dollar_volume')
 
    # Pick the top 10% of stocks ranked by dollar volume.
    high_dollar_volume = dollar_volume.percentile_between(90, 100)
    pipe.set_screen(high_dollar_volume)

    return pipe
 
def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = pipeline_output('my_pipeline')
  
    # These are the securities that we are interested in trading each day.
    context.security_list = context.output.index
    context.long_list = context.output[(context.output['ewma15'] >= context.output['ewma120']) & (context.output['yes_price'] < context.output['ewma15'])]
    context.short_list = context.output[(context.output['ewma15'] < context.output['ewma120']) & (context.output['yes_price'] > context.output['ewma15'])]
    
def my_assign_weights(context):
    """
    Assign weights to securities that we want to order.
    """
    long_weight, short_weight = 0, 0
    if len(context.long_list) != 0:
        long_weight = context.long_leverage / len(context.long_list)
    if len(context.short_list) != 0:
        short_weight = context.short_leverage / len(context.short_list)
    return long_weight, short_weight
 
def my_rebalance(context,data):
    """
    Execute orders according to our schedule_function() timin. 
    """
    for stock in context.portfolio.positions:
        if data.can_trade(stock):
            history_price_long = data.history(stock, 'price', context.look_back_long, '1d')
            stock_ewma120 = talib.EMA(history_price_long.values, timeperiod=context.look_back_long)[-1]
            
            history_price_short = data.history(stock, 'price', context.look_back_short, '1d')
            stock_ewma15 = talib.EMA(history_price_short.values, timeperiod=context.look_back_short)[-1]
            
            ema_diff = abs(stock_ewma120 - stock_ewma15)
            
            stock_cur_price = data.current(stock, 'price')
            stock_yes_price = data.history(stock, 'price', 2, '1d').values[0]
            stock_position = context.portfolio.positions[stock]
            stock_buy_price = stock_position.cost_basis
            
            # less than 0 means short
            if stock_position.amount < 0:
                if ema_diff > (0.06 * stock_cur_price) \
                    and stock_yes_price < stock_ewma15 \
                    and stock_cur_price > stock_ewma15:
                        # close
                        order_target_percent(stock, 0)
                elif stock_yes_price > (stock_buy_price * 1.1):
                    # close
                    order_target_percent(stock, 0)
            else:
                if ema_diff > (0.06 * stock_cur_price) \
                    and stock_yes_price > stock_ewma15 \
                    and stock_cur_price < stock_ewma15:
                        # close
                        order_target_percent(stock, 0)
                elif stock_yes_price < (stock_buy_price * 0.9):
                    # close
                    order_target_percent(stock, 0)
     
    long_weight, short_weight = my_assign_weights(context)
    for stock in context.security_list:
        if data.can_trade(stock):
            if stock in context.long_list.index:
                stock_ewma15 = context.long_list['ewma15'][stock]
                cur_price = data.current(stock, 'price')
                if cur_price >= stock_ewma15:
                    order_target_percent(stock, long_weight)
            elif stock in context.short_list.index:
                stock_ewma15 = context.short_list['ewma15'][stock]
                cur_price = data.current(stock, 'price')
                if cur_price < stock_ewma15:
                    order_target_percent(stock, short_weight)


def my_record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    pass
 
def handle_data(context,data):
    """
    Called every minute.
    """
    pass
