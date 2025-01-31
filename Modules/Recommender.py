from Modules.Data import *
import pandas as pd

def content_based_recommender(dropdown_option, platform, min_score, how_many, sort_option, min_year):
    df_main = get_df_main()
    df_img = get_df_img()
    df_desc = get_df_desc()
    df_supp = get_df_supp()

    print("\nShape of df_main : {}".format(df_main.shape))
    print("\nShape of df_img : {}".format(df_img.shape))
    print("\nShape of df_desc : {}".format(df_desc.shape))

    print(df_main.head(5))

    # Get the cosine similarities
    cosine_similarities = get_cosine_similarities()
    # print("Cosine Similarities : {}".format(cosine_similarities))

    # Return closest game title match
    closest_title, distance_score = find_closest_title(df_main, dropdown_option)
    print("\nClosest Title : {}".format(closest_title))

    # Create a Dataframe with these column headers
    columns = ["Game Title", "Year", "Score", "Weighted Score", "Total Ratings", "App Id", "Header Image", "Description", "Url"]
    recommendations_df = pd.DataFrame(columns=columns)

    # Make the closest title whichever dropdown option the user has chosen
    closest_title = dropdown_option

    # Find the corresponding index of the game title
    games_index = get_index_from_title(df_main, closest_title)
    print("\ngames_index : {}".format(games_index))

    # Return the list of the indices of the most similar games
    games_list = list(enumerate(cosine_similarities[int(games_index)]))
    print("\nLength of games_list : {}".format(len(games_list)))
    
    # Sort the list of similar games from top to bottom
    similar_games = list(filter(lambda x: x[0] != int(games_index), sorted(games_list, key=lambda x: x[1], reverse=True)))
    print("\nLength of similar_games : {}".format(len(similar_games)))

    # Filter the games that are on selected platform
    filtered_games_platform = []
    for i, s in similar_games:
        if platform in get_platform_from_index(df_main, i):
            filtered_games_platform.append((i, s))
    print("\nLength of filtered_games_platform : {}".format(len(filtered_games_platform)))

    # Only return the games that are above the minimum score
    filtered_games_minimum_score = []
    for i, s in filtered_games_platform:
        if get_score_from_index(df_main, i) > min_score:
            filtered_games_minimum_score.append((i, s))
    print("\nLength of filtered_games_minimum_score : {}".format(len(filtered_games_minimum_score)))

    # Return the game tuple (game index, game distance score) and store in a dataframe
    for i, s in filtered_games_minimum_score[:how_many]:
        app_id = get_app_id_from_index(df_main, i)
        
        # Dataframe will contain attributes based on game index
        row = {
            "App Id": app_id,
            "Game Title": get_title_from_index(df_main, i),
            "Header Image": get_img_from_app_id(df_img, app_id),
            "Description": get_desc_from_app_id(df_desc, app_id), 
            "Year": get_title_year_from_index(df_main, i),
            "Score": get_score_from_index(df_main, i),
            "Weighted Score": get_weighted_score_from_index(df_main, i),
            "Total Ratings": get_total_ratings_from_index(df_main, i),
            "Url": get_url_from_app_id(df_supp, app_id),
            }

        # Append each row to the recommendations dataframe
        recommendations_df = pd.concat([recommendations_df, pd.DataFrame([row])], ignore_index=True)

    # Sort dataframe by sort_option provided by user
    recommendations_df = recommendations_df.sort_values(sort_option, ascending=False)
    
    # Only include games released in the same or after the minimum year selected
    recommendations_df = recommendations_df[recommendations_df["Year"] >= min_year]

    print("\nShape of recommendations_df : {}".format(recommendations_df.shape))

    return recommendations_df
