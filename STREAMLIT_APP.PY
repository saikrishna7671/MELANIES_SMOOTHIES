
# Import python packages
import streamlit as st

import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col


# Get active Snowflake session
cnx = st.connection("snowflake")
session = cnx.session()

# App title
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")

st.write(
    """
    Choose the fruits you want in your custom Smoothie!
    """
)

# Enter customer name
name_on_order = st.text_input('Name on Smoothie:')

st.write('The name on your Smoothie will be:', name_on_order)

# Fetch fruit options
my_dataframe = session.table(
    "smoothies.public.fruit_options"
)

fruit_options = [
    row["FRUIT_NAME"]
    for row in my_dataframe.select(col("FRUIT_NAME")).collect()
]

# Select ingredients
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe,
    max_selections=5
)

if ingredients_list:

    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

    # Create INSERT statement
    my_insert_stmt = """
        INSERT INTO smoothies.public.orders
        (ingredients, name_on_order)
        VALUES (?, ?)
    """

    # Submit Order button
    time_to_insert = st.button('Submit Order')

    if time_to_insert:

        if not name_on_order.strip():
            st.warning("Please enter your name.")

        else:
            session.sql(
                my_insert_stmt,
                params=[ingredients_string, name_on_order]
            ).collect()

            st.success(
                'Your Smoothie is ordered!',
                icon='✅'
            )
