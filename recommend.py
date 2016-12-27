# coding=utf-8
from collections import defaultdict
import sys
import random
import math
from operator import itemgetter


class UserBasedCF():
    def __init__(self):
        self.trainsetRating = {}
        self.testsetRating = {}
        self.trainsetTime = {}
        self.testsetTime = {}

        self.n_sim_user = 20
        self.n_rec_movie = 20

        self.user_sim_mat_cosin = {}
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
        ''' calculate user similarity matrix '''
        # build inverse table for item-users
        # key=movieID, value=list of userIDs who have seen this movie
        # print >> sys.stderr, 'building movie-users inverse table...'
        movie2users = dict()

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

        # count co-rated items between users
        usersim_mat = self.user_sim_mat_cosin
        # print >> sys.stderr, 'building user co-rated movies matrix...'
        # movieId set(Users)
        for movie, users in movie2users.iteritems():
            for u in users:
                for v in users:
                    if u == v: continue
                    usersim_mat.setdefault(u, {})
                    usersim_mat[u].setdefault(v, 0)
                    usersim_mat[u][v] += 1
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
        # print >> sys.stderr, 'Evaluation start...'

        N = self.n_rec_movie
        #  varables for precision and recall
        hit = 0
        rec_count = 0
        test_count = 0
        # varables for coverage
        all_rec_movies = set()
        # varables for popularity
        popular_sum = 0

        # TrainsetRating 344{'3948': 3, '2734': 2}
        for user, id2Rating in self.trainsetRating.items():
            # TrainsetRating 344{'3948': 3, '2734': 2}
            test_movies = self.testsetRating.get(user, {})
            rec_movies = self.recommend(user)
            for movie, w in rec_movies:
                if movie in test_movies:
                    hit += 1
                all_rec_movies.add(movie)
                popular_sum += math.log(1 + self.movie_popular[movie])
            rec_count += N
            test_count += len(test_movies)
        # precision = hit / (20 * userCount)
        precision = hit / (1.0 * rec_count)
        # recall = hit / sum(每个人看的test电影的求和)
        recall = hit / (1.0 * test_count)
        coverage = len(all_rec_movies) / (1.0 * self.movie_count)
        popularity = popular_sum / (1.0 * rec_count)

        # print >> sys.stderr, 'neighbor=%d\tprecision=%.4f\trecall=%.4f\tcoverage=%.4f\tpopularity=%.4f' % \
        #                     (self.n_sim_user,precision, recall, coverage, popularity)
        print >> sys.stderr, '%d\t%.4f\t%.4f\t%.4f\t%.4f' % \
                             (self.n_sim_user, precision, recall, coverage, popularity)

    def calc_user_sim_peason(self):
        pass

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
        for v, wuv in sorted(self.user_sim_mat_cosin[user].items(),
                             key=itemgetter(1), reverse=True)[0:K]:
            print v, wuv
            for movie in self.trainsetRating[v]:
                if movie in watched_movies:
                    continue
                # predict the user's "interest" for each movie
                rank.setdefault(movie, 0)
                rank[movie] += wuv
        # return the N best movies
        return sorted(rank.items(), key=itemgetter(1), reverse=True)[0:N]


if __name__ == '__main__':
    ratingfile = 'ml-1m/rating.dat'
    usercf = UserBasedCF()
    usercf.generate_dataset(ratingfile)
    usercf.calc_user_sim_cosin()
    usercf.evaluate()
