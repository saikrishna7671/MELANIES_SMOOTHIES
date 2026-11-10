
# ==========================================
# 1. IMPORT LIBRARIES
# ==========================================

import streamlit as st
import pandas as pd
import requests

from urllib.parse import quote
from snowflake.snowpark.functions import col


# ==========================================
# 2. SNOWFLAKE CONNECTION
# ==========================================

cnx = st.connection("snowflake")
session = cnx.session()


# ==========================================
# 3. APPLICATION TITLE
# ==========================================

st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")

st.write("Choose the fruits you want in your custom Smoothie!")


# ==========================================
# 4. CUSTOMER NAME
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
    "SMOOTHIES.PUBLIC.FRUIT_OPTIONS"
).select(
    col("FRUIT_NAME"),
    col("SEARCH_ON")
)


# ==========================================
# 6. CONVERT SNOWPARK TO PANDAS
# ==========================================

pd_df = my_dataframe.to_pandas()


# ==========================================
# 7. DISPLAY DATAFRAME (OPTIONAL DEBUGGING)
# ==========================================

# st.dataframe(pd_df, use_container_width=True)
# st.stop()


# ==========================================
# 8. MULTISELECT INGREDIENTS
# ==========================================

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    pd_df["FRUIT_NAME"].tolist(),
    max_selections=5
)


# ==========================================
# 9. PROCESS SELECTED INGREDIENTS
# ==========================================

if ingredients_list:

    ingredients_string = ""

    for fruit_chosen in ingredients_list:

        ingredients_string += fruit_chosen + " "

        # ==================================
        # 10. GET API NAME USING PANDAS LOC
        # ==================================

        matching_fruit = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ]

        if matching_fruit.empty or pd.isna(matching_fruit.iloc[0]):

            st.error(
                f"No SEARCH_ON value configured for {fruit_chosen}"
            )

            continue

        search_on = str(matching_fruit.iloc[0]).strip()

        st.write(
            "The search value for",
            fruit_chosen,
            "is",
            search_on,
            "."
        )

        # ==================================
        # 11. DISPLAY NUTRITION HEADING
        # ==================================

        st.subheader(
            fruit_chosen + " Nutrition Information"
        )

        # ==================================
        # 12. DYNAMIC FRUITYVICE API CALL
        # ==================================

        api_url = (
            "https://www.fruityvice.com/api/fruit/"
            + quote(search_on, safe="")
        )

        try:

            fruityvice_response = requests.get(
                api_url,
                timeout=20
            )

            # Check API response status
            fruityvice_response.raise_for_status()

            # Convert API JSON into Pandas DataFrame
            fruit_data = fruityvice_response.json()

            fruit_df = pd.json_normalize(fruit_data)

            # Display nutrition information
            st.dataframe(
                fruit_df,
                use_container_width=True
            )

        except requests.exceptions.HTTPError:

            st.warning(
                f"{search_on} was not found in the API database."
            )

        except requests.exceptions.RequestException as e:

            st.error(
                f"API connection error: {e}"
            )

        except ValueError:

            st.error(
                f"Invalid API response for {search_on}."
            )


    # ======================================
    # 13. SUBMIT SMOOTHIE ORDER
    # ======================================

    st.divider()

    if st.button("Submit Order"):

        if not name_on_order.strip():

            st.warning("Please enter your name.")

        else:

            my_insert_stmt = """
                INSERT INTO SMOOTHIES.PUBLIC.ORDERS
                (INGREDIENTS, NAME_ON_ORDER)
                VALUES (?, ?)
            """

            try:

                session.sql(
                    my_insert_stmt,
                    params=[
                        ingredients_string.strip(),
                        name_on_order.strip()
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

else:

    st.info("Please select at least one fruit.")
