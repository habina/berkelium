"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume
import talib
import numpy as np

def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    # current position, 0 stands for empty exposure, 1 stands for full exposure
    context.pos = 0
    
    # Rebalance every day, 1 hour after market open.
    schedule_function(my_rebalance, date_rules.every_day(), time_rules.market_open(hours=2))
     
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
     
    # Create a dollar volume factor.
    # dollar_volume = AverageDollarVolume(window_length=1)
    # pipe.add(dollar_volume, 'dollar_volume')
 
    # Pick the top 1% of stocks ranked by dollar volume.
    # high_dollar_volume = dollar_volume.percentile_between(99, 100)
    # pipe.set_screen(high_dollar_volume)
    
    return pipe
 
def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    # context.output = pipeline_output('my_pipeline')
  
    # These are the securities that we are interested in trading each day.
    # context.security_list = context.output.index
    
    # ema short term
    ema_short_term_look_back = 20
    # ema long term
    ema_long_term_look_back = 120
    # ema middle term
    ema_middle_term_look_back = 60
    # short volumn look back
    short_volume_look_back = 12
    
    context.spy = sid(40555)
    context.security_list = [context.spy]
    history_price_short = data.history(context.spy, 'price', ema_short_term_look_back, '1d')
    context.ema_short_price = talib.EMA(history_price_short.values, timeperiod=ema_short_term_look_back)[-1]

    history_price_long = data.history(context.spy, 'price', ema_long_term_look_back, '1d')
    context.ema_long_price = talib.EMA(history_price_long.values, timeperiod=ema_long_term_look_back)[-1]
    
    hitory_price_middle = data.history(context.spy, 'price', ema_middle_term_look_back, '1d')

    context.ema_middle_price = talib.EMA(hitory_price_middle.values, timeperiod=ema_middle_term_look_back)[-1]

    history_volume_short = data.history(context.spy, 'volume', short_volume_look_back, '1d')
    context.ema_short_volume = talib.EMA(history_volume_short.values, timeperiod=short_volume_look_back)[-1]
    # context.ema_short_volume = history_volume_short.mean()
   
    
def my_assign_weights(context, data):
    """
    Assign weights to securities that we want to order.
    """
    pass
 
def my_rebalance(context,data):
    """
    Execute orders according to our schedule_function() timin. 
    """
    
    bug_signal = 0
    hold_signal = 0
    sell_signal = 0
    
    cur_price = data.current(context.spy, 'price')
    today_volume = np.sum(data.history(context.spy, 'volume', 345, '1m').values)
    yes_volume = np.sum(data.history(context.spy, 'volume', 1, '1d').values)
    if context.pos == 0:
        if context.ema_short_price > context.ema_middle_price \
        and context.ema_middle_price > context.ema_long_price \
        and cur_price > context.ema_middle_price:
        # and today_volume > (context.ema_short_volume * 0.5):
            bug_signal = 1
            order_target_percent(context.spy, 1)
            context.pos = 1
        if context.ema_short_price < context.ema_middle_price \
        and context.ema_middle_price < context.ema_long_price \
        and cur_price < context.ema_middle_price:
            order_target_percent(context.spy, -1)
            context.pos = -1
    elif context.pos == 1:
        if context.ema_short_price > context.ema_middle_price \
            and context.ema_middle_price > context.ema_long_price \
            and cur_price > context.ema_short_price:
                hold_signal = 1
        else:
            close_signal = 1
            order_target_percent(context.spy, 0)
            context.pos = 0
    elif context.pos == -1:
        if context.ema_short_price < context.ema_middle_price \
            and context.ema_middle_price < context.ema_long_price \
            and cur_price < context.ema_short_price:
                hold_signal = -1
        else:
            close_signal = -1
            order_target_percent(context.spy, 0)
            context.pos = 0
 
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
