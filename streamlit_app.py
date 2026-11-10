
# ==========================================
# 1. IMPORT PYTHON PACKAGES
# ==========================================

import streamlit as st
from snowflake.snowpark.functions import col
import requests

# ==========================================
# 2. GET ACTIVE SNOWFLAKE CONNECTION
# ==========================================

cnx = st.connection("snowflake")
session = cnx.session()

# ==========================================
# 3. APP TITLE
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
# 6. SELECT INGREDIENTS
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
        # 8. DISPLAY FRUIT NUTRITION TITLE
        # ==================================

        st.subheader(
            fruit_chosen + " Nutrition Information"
        )

        # ==================================
        # 9. DYNAMIC API CALL
        # ==================================

        try:

            smoothiefroot_response = requests.get(
                "https://my.smoothiefroot.com/api/fruit/"
                + fruit_chosen.lower(),
                timeout=15
            )

            # ==================================
            # 10. CONVERT JSON INTO DATAFRAME
            # ==================================

            response_data = smoothiefroot_response.json()

            sf_df = st.dataframe(
                data=response_data,
                use_container_width=True
            )

        except requests.exceptions.RequestException as e:

            st.error(
                f"API connection failed for {fruit_chosen}: {e}"
            )

        except ValueError:

            st.error(
                f"Invalid API response for {fruit_chosen}"
            )

    # ======================================
    # 11. CREATE INSERT STATEMENT
    # ======================================

    my_insert_stmt = """
        INSERT INTO smoothies.public.orders
        (ingredients, name_on_order)
        VALUES (?, ?)
    """

    # ======================================
    # 12. SUBMIT ORDER
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
