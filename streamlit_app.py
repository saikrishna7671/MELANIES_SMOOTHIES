
import streamlit as st
import pandas as pd
import requests

from snowflake.snowpark.functions import col


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Customize Your Smoothie",
    page_icon="🥤",
    layout="wide"
)


# --------------------------------------------------
# 2. SNOWFLAKE CONNECTION
# --------------------------------------------------

@st.cache_resource
def get_snowflake_session():

    conn = st.connection("snowflake")

    return conn.session()


try:
    session = get_snowflake_session()

except Exception as e:
    st.error("Unable to connect to Snowflake.")
    st.exception(e)
    st.stop()


# --------------------------------------------------
# 3. APPLICATION TITLE
# --------------------------------------------------

st.title("🥤 Customize Your Smoothie! 🥤")

st.write(
    "Choose the fruits you want in your custom smoothie!"
)


# --------------------------------------------------
# 4. GET SMOOTHIE NAME
# --------------------------------------------------

smoothie_name = st.text_input(
    "Name on Smoothie:",
    placeholder="Enter your name"
)

if smoothie_name:
    st.write(
        f"The name on your Smoothie will be: {smoothie_name}"
    )


# --------------------------------------------------
# 5. READ FRUIT OPTIONS FROM SNOWFLAKE
# --------------------------------------------------

try:

    my_dataframe = (
        session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
        .select(
            col("FRUIT_NAME"),
            col("SEARCH_ON")
        )
    )

    # Convert Snowpark DataFrame to Pandas DataFrame

    pd_df = my_dataframe.to_pandas()

except Exception as e:

    st.error("Unable to read FRUIT_OPTIONS table.")

    st.exception(e)

    st.stop()


# --------------------------------------------------
# 6. DISPLAY FRUIT OPTIONS
# --------------------------------------------------

if pd_df.empty:

    st.warning("No fruits available in the database.")

    st.stop()


# Remove rows without fruit names

pd_df = pd_df.dropna(subset=["FRUIT_NAME"])

fruit_options = pd_df["FRUIT_NAME"].astype(str).tolist()


# --------------------------------------------------
# 7. MULTISELECT WIDGET
# --------------------------------------------------

ingredients_list = st.multiselect(

    "Choose up to 5 ingredients:",

    fruit_options,

    max_selections=5

)


# --------------------------------------------------
# 8. GET NUTRITION INFORMATION USING API
# --------------------------------------------------

ingredients_string = ""


if ingredients_list:

    for fruit_chosen in ingredients_list:

        ingredients_string += fruit_chosen + " "

        # Find corresponding SEARCH_ON value

        matching_rows = pd_df.loc[
            pd_df["FRUIT_NAME"] == fruit_chosen,
            "SEARCH_ON"
        ]

        # Check whether mapping exists

        if matching_rows.empty or pd.isna(matching_rows.iloc[0]):

            st.error(
                f"SEARCH_ON value is missing for {fruit_chosen}"
            )

            continue

        search_on = str(matching_rows.iloc[0]).strip()

        if not search_on:

            st.error(
                f"SEARCH_ON value is empty for {fruit_chosen}"
            )

            continue

        # Display fruit heading

        st.subheader(
            fruit_chosen + " Nutrition Information"
        )

        # API request

        try:

            smoothiefruit_response = requests.get(

                f"https://my.smoothiefroot.com/api/fruit/{search_on}",

                timeout=15

            )

            smoothiefruit_response.raise_for_status()

            response_data = smoothiefruit_response.json()

            # Handle API response

            if isinstance(response_data, dict) and "error" in response_data:

                st.warning(response_data["error"])

            elif isinstance(response_data, (dict, list)):

                sf_df = pd.DataFrame(response_data)

                st.dataframe(
                    sf_df,
                    use_container_width=True
                )

            else:

                st.warning(
                    f"No nutrition information found for {fruit_chosen}"
                )

        except requests.exceptions.Timeout:

            st.error(
                f"API request timed out for {fruit_chosen}"
            )

        except requests.exceptions.RequestException as e:

            st.error(
                f"API request failed for {fruit_chosen}: {e}"
            )

        except ValueError:

            st.error(
                f"Invalid JSON response for {fruit_chosen}"
            )


# --------------------------------------------------
# 9. SUBMIT ORDER
# --------------------------------------------------

st.divider()

if st.button("Submit Order"):

    if not smoothie_name.strip():

        st.warning("Please enter your name.")

    elif not ingredients_list:

        st.warning("Please select at least one fruit.")

    else:

        try:

            # Store ingredients and name in Snowflake

            insert_query = """
                INSERT INTO SMOOTHIES.PUBLIC.ORDERS
                (INGREDIENTS, NAME_ON_ORDER)
                VALUES (?, ?)
            """

            session.sql(
                insert_query,
                params=[
                    ingredients_string.strip(),
                    smoothie_name.strip()
                ]
            ).collect()

            st.success(
                f"Order successfully submitted for {smoothie_name}!"
            )

            st.balloons()

        except Exception as e:

            st.error("Unable to submit your order.")

            st.exception(e)


# --------------------------------------------------
# 10. CLOSE APPLICATION
# --------------------------------------------------

st.caption(
    "Powered by Streamlit, Snowflake Snowpark and SmoothieFroot API"
)
