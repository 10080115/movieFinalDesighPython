# coding=utf-8
from collections import defaultdict
import sys
import random
import math
from operator import itemgetter
from math import sqrt


class UserBasedCF():
    def __init__(self):
        self.trainsetRating = {}
        self.testsetRating = {}
        self.trainsetTime = {}
        self.testsetTime = {}
        self.count = 0

        self.n_sim_user = 2
        self.n_rec_movie = 20

        self.movie2users = {}
        self.user_sim_mat = {}
        self.movie_popular = {}
        self.movie_count = 0

        print >> sys.stderr, 'Similar user number = %d' % self.n_sim_user
        print >> sys.stderr, 'recommended movie number = %d' % self.n_rec_movie

    @staticmethod
    def loadfile(filename):
        ''' load a file, return a generator. '''
        fp = open(filename, 'r')
        for i, line in enumerate(fp):
            yield line.strip('\r\n')
        fp.close()
        print >> sys.stderr, 'load %s succ' % filename

    def sim_pearson(self, p1, p2):
        self.count += 1
        if self.count % 500000 == 0:
            print self.count
        prefs = self.trainsetRating
        # Get the list of mutually rated items
        si = {}
        for item in prefs[p1]:
            if item in prefs[p2]:
                si[item] = 1
                # if they are no ratings in common, return 0
        if len(si) == 0:
            return 0
            # Sum calculations
        n = len(si)

        # Sums of all the preferences
        sum1 = sum([prefs[p1][it] for it in si])
        sum2 = sum([prefs[p2][it] for it in si])

        # Sums of the squares
        sum1Sq = sum([pow(prefs[p1][it], 2) for it in si])
        sum2Sq = sum([pow(prefs[p2][it], 2) for it in si])

        # Sum of the products
        pSum = sum([prefs[p1][it] * prefs[p2][it] for it in si])

        # Calculate r (Pearson score)
        num = pSum - (sum1 * sum2 / n)
        den = sqrt((sum1Sq - pow(sum1, 2) / n) * (sum2Sq - pow(sum2, 2) / n))
        if den == 0:
            return 0

        r = num / den

        return r

    def generate_dataset(self, filename, pivot=0.8):
        ''' load rating data and split it to training set and test set '''
        trainset_len = 0
        testset_len = 0

        for line in self.loadfile(filename):
            user, movie, rating, timestamp = line.split('::')
            # split the data by pivot
            if (random.random() < pivot):
                self.trainsetRating.setdefault(user, {})
                self.trainsetTime.setdefault(user, {})
                self.trainsetRating[user][movie] = int(rating)
                self.trainsetTime[user][movie] = int(timestamp)
                trainset_len += 1
            else:
                self.testsetRating.setdefault(user, {})
                self.testsetTime.setdefault(user, {})
                self.testsetRating[user][movie] = int(rating)
                self.testsetTime[user][movie] = int(timestamp)
                testset_len += 1

        print >> sys.stderr, 'split training set and test set succ'
        print >> sys.stderr, 'train set = %s' % trainset_len
        print >> sys.stderr, 'test set = %s' % testset_len

    def calc_user_sim_cosin(self):
        movie2users = self.movie2users
        # count co-rated items between users
        usersim_mat = self.user_sim_mat
        # print >> sys.stderr, 'building user co-rated movies matrix...'
        # movieId set(Users)
        for movie, users in movie2users.iteritems():
            for u in users:
                for v in users:
                    if u == v:
                        continue
                    if u > v:
                        self.count += 1
                        if self.count % 50000000 == 0:
                            print self.count
                        usersim_mat.setdefault(u, {})
                        usersim_mat.setdefault(v, {})
                        usersim_mat[u].setdefault(v, 0)
                        usersim_mat[v].setdefault(u, 0)
                        usersim_mat[u][v] += 1
                        usersim_mat[v][u] += 1
                    else:
                        continue
        print >> sys.stderr, 'build user co-rated movies matrix succ'

        # calculate similarity matrix
        # print >> sys.stderr, 'calculating user similarity matrix...'
        simfactor_count = 0
        for u, related_users in usersim_mat.iteritems():
            for v, count in related_users.iteritems():
                usersim_mat[u][v] = count / math.sqrt(
                    len(self.trainsetRating[u]) * len(self.trainsetRating[v]))
                simfactor_count += 1

        print >> sys.stderr, 'calculate user similarity matrix(similarity factor) succ'
        print >> sys.stderr, 'Total similarity factor number = %d' % simfactor_count

    def evaluate(self):
        ''' return precision, recall, coverage and popularity '''
        print >> sys.stderr, 'Evaluation start...'

        N = self.n_rec_movie
        #  varables for precision and recall
        hit = 0
        rec_count = 0
        test_count = 0
        # varables for coverage
        all_rec_movies = set()
        # varables for popularity
        popular_sum = 0

        i = 0
        for user, id2Rating in self.trainsetRating.items():
            if i == 500:
                print >> sys.stderr, 'recommended for %d users' % i
            i += 1
            test_movies = self.testsetRating.get(user, {})
            rec_movies = self.recommend(user)
            for movie, w in rec_movies:
                if movie in test_movies:
                    hit += 1
                all_rec_movies.add(movie)
                popular_sum += math.log(1 + self.movie_popular[movie])
            rec_count += N
            test_count += len(test_movies)
        precision = hit / (1.0 * rec_count)
        # recall = hit / sum(每个人看的test电影的求和)
        recall = hit / (1.0 * test_count)
        coverage = len(all_rec_movies) / (1.0 * self.movie_count)
        popularity = popular_sum / (1.0 * rec_count)

        # print >> sys.stderr, 'neighbor=%d\tprecision=%.4f\trecall=%.4f\tcoverage=%.4f\tpopularity=%.4f' % \
        #                     (self.n_sim_user,precision, recall, coverage, popularity)
        print >> sys.stderr, '%d\t%.4f\t%.4f\t%.4f\t%.4f' % \
                             (self.n_sim_user, precision, recall, coverage, popularity)

    def calc_user_sim_pearson(self):
        user_sim_mat_pearson = self.user_sim_mat
        movie2users = self.movie2users
        for movie, users in movie2users.iteritems():
            for u in users:
                for v in users:
                    if u == v:
                        continue
                    if u > v:
                        user_sim_mat_pearson.setdefault(u, {})
                        user_sim_mat_pearson.setdefault(v, {})
                        r = self.sim_pearson(u, v)
                        user_sim_mat_pearson[u][v] = r
                        user_sim_mat_pearson[v][u] = r
                    else:
                        continue

    def foreachMap(self, rating, time):
        for userId, Id2Rating in rating.items():
            for mId, rating in Id2Rating.items():
                print userId, mId, rating, time[userId][mId]

    def recommend(self, user):
        ''' Find K similar users and recommend N movies. '''
        K = self.n_sim_user
        N = self.n_rec_movie
        rank = dict()
        watched_movies = self.trainsetRating[user]
        # v=similar user, wuv=similarity factor
        for v, wuv in sorted(self.user_sim_mat[user].items(),
                             key=itemgetter(1), reverse=True)[0:K]:
            for movie in self.trainsetRating[v]:
                if movie in watched_movies:
                    continue
                # predict the user's "interest" for each movie
                rank.setdefault(movie, 0)
                rank[movie] += wuv * self.trainsetRating[v][movie]
        # return the N best movies
        return sorted(rank.items(), key=itemgetter(1), reverse=True)[0:N]

    def reverse_table(self):
        ''' calculate user similarity matrix '''
        # build inverse table for item-users
        # key=movieID, value=list of userIDs who have seen this movie
        # print >> sys.stderr, 'building movie-users inverse table...'

        movie2users = self.movie2users

        for user, movies in self.trainsetRating.iteritems():
            for movie in movies:
                # inverse table for item-users
                if movie not in movie2users:
                    movie2users[movie] = set()
                movie2users[movie].add(user)
                # count item popularity at the same time
                if movie not in self.movie_popular:
                    self.movie_popular[movie] = 0
                self.movie_popular[movie] += 1
        # print >> sys.stderr, 'build movie-users inverse table succ'

        # save the total movie number, which will be used in evaluation
        self.movie_count = len(movie2users)
        print >> sys.stderr, 'total movie number = %d' % self.movie_count


if __name__ == '__main__':
    ratingfile = 'ml-1m/ratings.dat'
    usercf = UserBasedCF()
    usercf.generate_dataset(ratingfile)
    usercf.reverse_table()
    # usercf.calc_user_sim_cosin()
    usercf.calc_user_sim_pearson()
    usercf.n_sim_user = 20
    usercf.evaluate()
    print usercf.count
    # usercf.n_sim_user = 40
    # usercf.evaluate()
    # usercf.n_sim_user = 60
    # usercf.evaluate()
    # usercf.n_sim_user = 80
    # usercf.evaluate()
    # usercf.n_sim_user = 100
    # usercf.evaluate()
