
# ==========================================
# 1. IMPORT PYTHON PACKAGES
# ==========================================

import streamlit as st
from snowflake.snowpark.functions import col
import requests

# ==========================================
# 2. CONNECT TO SNOWFLAKE
# ==========================================

cnx = st.connection("snowflake")
session = cnx.session()

# ==========================================
# 3. STREAMLIT APP TITLE
# ==========================================

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")

st.write(
    """
    Choose the fruits you want in your custom Smoothie!
    """
)

# ==========================================
# 4. ENTER CUSTOMER NAME
# ==========================================

name_on_order = st.text_input("Name on Smoothie:")

st.write(
    "The name on your Smoothie will be:",
    name_on_order
)

# ==========================================
# 5. FETCH FRUIT OPTIONS FROM SNOWFLAKE
# ==========================================

my_dataframe = session.table(
    "smoothies.public.fruit_options"
)

fruit_options = [
    row["FRUIT_NAME"]
    for row in my_dataframe.select(
        col("FRUIT_NAME")
    ).collect()
]

# ==========================================
# 6. SELECT UP TO 5 INGREDIENTS
# ==========================================

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    fruit_options,
    max_selections=5
)

# ==========================================
# 7. PROCESS SELECTED INGREDIENTS
# ==========================================

if ingredients_list:

    ingredients_string = ""

    for fruit_chosen in ingredients_list:

        ingredients_string += fruit_chosen + " "

        # ==================================
        # 8. CALL SMOOTHIEFR00T API
        # ==================================

        try:

            smoothiefroot_response = requests.get(
                "https://my.smoothiefroot.com/api/fruit/watermelon",
                timeout=15
            )

            smoothiefroot_response.raise_for_status()

            # Convert JSON response into DataFrame
            sf_df = st.dataframe(
                data=smoothiefroot_response.json(),
                use_container_width=True
            )

        except requests.exceptions.RequestException as e:

            st.error(
                f"Unable to fetch nutrition information: {e}"
            )

        except ValueError:

            st.error("Invalid JSON response from API.")

    # ======================================
    # 9. CREATE INSERT STATEMENT
    # ======================================

    my_insert_stmt = """
        INSERT INTO smoothies.public.orders
        (ingredients, name_on_order)
        VALUES (?, ?)
    """

    # ======================================
    # 10. SUBMIT ORDER BUTTON
    # ======================================

    time_to_insert = st.button("Submit Order")

    if time_to_insert:

        if not name_on_order.strip():

            st.warning("Please enter your name.")

        else:

            try:

                session.sql(
                    my_insert_stmt,
                    params=[
                        ingredients_string.strip(),
                        name_on_order
                    ]
                ).collect()

                st.success(
                    "Your Smoothie is ordered!",
                    icon="✅"
                )

            except Exception as e:

                st.error(
                    f"Unable to submit order: {e}"
                )
