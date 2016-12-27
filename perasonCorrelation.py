from collections import defaultdict
import sys
import random
import math
from operator import itemgetter


def load_data():
    filename_user_movie = './ml-1m/ratings.dat'

    user_movie_rating_timestamp = {}
    # {'1': {'1287': '5:978302039', '594': '4:978302268', '1193': '5:978300760', '1197': '3:978302268', '919': '4:978301368', '661': '3:978302109', '3408': '4:978300275', '914': '3:978301968', '2804': '5:978300719', '2355': '5:978824291'}}
    size = 0
    for line in open(filename_user_movie):
        if size < 100:
            size += 1
            (userId, itemId, rating, timestamp) = line.strip('\n').split('::')
            user_movie_rating_timestamp.setdefault(userId, [])
            user_movie_rating_timestamp[userId].append(itemId + ':' + rating + ':' + timestamp)  # movies = {}

    print user_movie_rating_timestamp

    # for user, item in user_movie_rating_timestamp:
    #     for rating, x in user_movie_rating_timestamp[user]:
    #         print rating

    return user_movie_rating_timestamp


# for line in open(filename_movieInfo):
#     (movieId, movieTitle) = line.split('|')[0:2]
#     movies[movieId] = movieTitle
def SplitData(ratingData, M):
    seed = 10

    key = 10

    test = defaultdict(list)
    train = defaultdict(list)
    random.seed(seed)
    user = set()
    for user, item in ratingData:
        if random.randint(0, M) == key or random.randint(0, M) + 1 == key:
            test[user].append(item)
            print user
        else:
            train[user].append(item)
    for i in user:
        print i
    return train, test


if __name__ == "__main__":
    M = 10
    user_movie_rating_timestamp = load_data()
    train, test = SplitData(user_movie_rating_timestamp, M)
