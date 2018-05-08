import numpy as np
import random as rnd
import matplotlib.pyplot as plt
import tri_modif_solver as slv

# CH = change if implementing on a new structure

class Individual:
    def __init__(self):

        "Structural dimentions"""
        a = 2.5  #CH
        h = np.sqrt(pow(a, 2) - pow(a/2, 2))  # triangle height  # CH

        "Original coordinates"
        xcoord = np.array([0, a, a/2])  # CH
        ycoord = np.array([0, 0, h])    # CH

        "Take a random number in range +-0.5m from the original coordinate"
        x1GA = rnd.randrange(np.round((xcoord[2] - 0.5)*10), np.round((xcoord[2] + 0.5)*10))/10
        y1GA = rnd.randrange(np.round((ycoord[2] - 0.5)*10), np.round((ycoord[2] + 0.5)*10))/10

        "New coordinates"
        xcoord = np.array([0, a, x1GA])    # CH
        ycoord = np.array([0, 0, y1GA])    # can use np.ix_?    # CH
        self.A = np.array(3 * [0.0225])    # area - each member 0.15x0.15m triangle  # CH
        self._plot_dict = None
        self._nodes = np.array([xcoord, ycoord])
        self._stress = 0
        self._fitness = 0
        self._probability = 0

    @property
    def stress(self):
        return self._stress

    @stress.setter
    def stress(self, new):
        self._stress = new

    @property
    def fitness(self):
        return self._fitness

    @fitness.setter
    def fitness(self, new):
        self._fitness = new

    @property
    def probability(self):
        return self._probability

    @probability.setter
    def probability(self,new):
        self._probability = new


class GA:
    def __init__(self, pop):
        self.mem_begin = np.array([0, 1, 2])  # beginning of an edge   # CH
        self.mem_end = np.array([1, 2, 0])  # end of an edge         # CH

        self._pool = list()
        self._popsize = pop

    def initial(self):
        for i in range(self._popsize):
            self._pool.append(Individual())
            print("nodes : {}".format(np.round([self._pool[i]._nodes[0, 2], self._pool[i]._nodes[1, 2]], 3)))
        print("......................")

    def calc(self):
        numelem = self.mem_begin.shape[0]  # count number of beginnings

        """Structural characteristics"""

        "Material characteristics E=(kPa), A=(m2)"
        E = np.array(self.mem_begin.shape[0] * [40000])  # modulus of elasticity for each member, now all concrete

        "Outside Forces [kN]"
        F = np.zeros((2*len(np.unique(self.mem_begin)), 1))  # forces vector
        F[2] = 10
        F[5] = 10

        "Fixed Degrees of Freedom (DOF)"
        dof_fixed = np.array([0, 1, 3])

        print("calculation")

        "Access solver"  #inner forces, stress, weight
        for i in range(self._popsize):
            pool = self._pool[i]
            # do res uloz veci, ktere returnuje, tuple 11 veci, globbing
            res = slv.stress(pool._nodes[0], pool._nodes[1], self.mem_begin, self.mem_end, numelem, E, pool.A, F, dof_fixed)
            stress, stress_normed, xi, xj, yi, yj, xinew, xjnew, yinew, yjnew, F_numnodex2, numnode = res
            pool._stress = stress
            plot_dict = {"xi":xi, "xj":xj, "yi":yi, "yj":yj, "xinew": xinew, "xjnew":xjnew, "yinew" : yinew, "yjnew":yjnew,
                         "F_numnodex2": F_numnodex2, "stress_normed": stress_normed, "numnode": numnode}
            pool._plot_dict = plot_dict

            pool._stress_max = np.round(np.max(pool._stress), 3)
            pool._probability = 0
            print(pool._stress)
            print("nodes : {}  stress_max : {}".format(np.round([pool._nodes[0, 2], pool._nodes[1, 2]], 3), pool._stress_max))

        print("...")

        for i in range(self._popsize):
            pool = self._pool[i]
            pool._weight = slv.weight(pool._nodes[0], pool._nodes[1], self.mem_begin, self.mem_end, pool.A)
            pool._probability = 0
            print("nodes : {}  weight_sum : {}".format(np.round([pool._nodes[0, 2], pool._nodes[1, 2]], 3), pool._weight))
        print("......................")

    def fitness(self):
        print("fitness")
        for i in range(self._popsize):
            self._pool[i]._fitness = self._pool[i]._stress_max / max(self._pool, key=lambda x: x._stress_max)._stress_max
        self._pool.sort(key=lambda x: x._fitness)  # lambda = jdi pres kazdy ind a dej mi fitness
        sum_fit = sum(map(lambda x: x._fitness, self._pool))

        """Define/create probability"""
        # create empty cell, i-times add a value at the end
        # higher individual fitness -> higher probab (a member will be chosen for a mutation with higher probability)
        # TODO: change either: better fitness - lower mutation probab or higher crossover probab
        probab = []
        for i in range(self._popsize):
            probab.append(sum_fit / self._pool[i]._fitness)
        sum_prob = sum(probab)

        """Probability record"""
        for i in range(self._popsize):
            pool = self._pool[i]
            # co konkretne dela tento radek?
            # todo: co je pool._probability?
            pool._probability = pool._probability + probab[i] / sum_prob
            print("nodes : {}  fit : {}  prob : {} ".format(np.round([pool._nodes[0, 2], pool._nodes[1, 2]], 3),
                                                            np.round(pool._fitness, 3),
                                                            np.round(pool._probability, 3)))
        print("..............")

    def crossover_top_3(self):
        selected_pool_x = list()
        selected_pool_y = list()
        select_num = 6  # 6x se vybere pravdepodobnost - projde se vsemi ind - pokud tri ma vetsi prob nez co se vybraly,
        #  tak se oba pridaji do selected pool
        possible_x = []
        possible_y = []
        #  vybereme vsechna mozna x a y ze vsech bodu
        for individual in self._pool:
            possible_x.append(individual._nodes[0, 2])
            possible_y.append(individual._nodes[1, 2])
        #  z teech x a y vybereme nahodne 3 x a 3 y
        selected_pool_x = np.random.choice(possible_x, 3)
        selected_pool_y = np.random.choice(possible_y, 3)

        #  Do firstch tri (tedy nejhorsich) ulozime nove x a nove y
        for i in range(3):
            self._pool[i]._nodes[0, 2] = selected_pool_x[i]  # / 2
            self._pool[i]._nodes[1, 2] = selected_pool_y[i]  # / 2
        for i in range(self._popsize):
            print([self._pool[i]._nodes[0, 2], self._pool[i]._nodes[1, 2]])
        print("___________________________________")

    def _switch(self, individual_pair, axis=0):
        # prohod hodnoty mezi 2 individualy
        # axis 0 -> prohod x
        # axis 1 -> prohod y

        # switch values between 2 individuals
        # axis 0 -> switch x
        # axis 1 -> switch y
        # todo: pomoc s komentovanim teto casti kodu

        first = individual_pair[0]
        second = individual_pair[1]
        tmp = first._nodes[axis, 2]  # temporary
        first._nodes[axis, 2] = second._nodes[axis, 2]
        second._nodes[axis, 2] = tmp

    def crossover(self):
        # vyber individualy co se prohodi
        # choose individuals that will switch
        # TODO: zakomponovat pravdepodobnost do np.random.choice
        probs = [x._probability for x in self._pool]
        switch_x = np.random.choice(self._pool, 2, replace=False, p=probs)  #vyber dvojice na prohozeni x
        switch_y = np.random.choice(self._pool, 2, replace=False, p=probs)

        "Areas Crossover"
        # different that for x and y, matrix with one column only
        # todo: Q: probehne crossover mezi stejnymi members, nebo naparuje dva jakekoliv clanky matice?
        switch_a =  np.random.choice(self._pool, 2, replace=False, p=probs)
        first_A = switch_a[0]
        second_A = switch_a[1]
        tmp = first_A.A
        first_A = second_A.A
        second_A = tmp

        self._switch(switch_x, 0)
        self._switch(switch_y, 1)

    def mutate(self, mutation_type):
        # create empty cell for probability
        probs = []  #  bude pole pravdepodobnosti

        for individual in self._pool:
            probs.append(individual._probability)  # append = pridej nakonec

        # pick a mutation candidate
        # todo: co znamena p=probs v dalsim radku?
        mutation_candidate = np.random.choice(self._pool, 1, p=probs)[0]
        possible_coefficients = [0.9, 0.9, 0.9, 1.1, 1.2, 0.8, 0.75, 1.3, 1.2, 1.1]
        coefficient = np.random.choice(possible_coefficients, 1)

        if mutation_type == "x":
            mutation_candidate._nodes[0, 2] = mutation_candidate._nodes[0, 2] * coefficient
        if mutation_type == "y":
            mutation_candidate._nodes[1, 2] = mutation_candidate._nodes[1, 2] * coefficient
        if mutation_type == "a":
            # TODO: mutovat kazdou osu zvlast, cim vetsi napeti v ose, tim vetsi prurez
            # TODO: dat maximalni a minimalni hodnoty A, x, y
            # TODO: jakou probob mutuje? tu nejhorsi nebo nejlepsi?
            for i in range(self._popsize):
                se = np.argmin(self._pool[i]._stress)
                mutation_candidate.A[se] = mutation_candidate.A[se] * 0.93  # vem prurez s min stress a zmensi ho o 7%
                # TODO: jaky by byl lepsi zpusob, dostat lepsi member?
                print(mutation_candidate.A)
    # not sure if completely correct logic with A... Check the results,


    def mutate_worst(self):
        possible_coefficients = [0.9, 1.1, 1.2, 0.8, 0.75, 1.3, 1.2]
        # todo: vyber z possible_coef 1 cislo?
        x_coefficient = np.random.choice(possible_coefficients, 1)
        y_coefficient = np.random.choice(possible_coefficients, 1)
        choice = np.random.randint(0, 3)
        # take a member and multiply it by a coef - change previous value for a new one
        # same as self._pool[choice]._nodes[0, 2] = self._pool[choice]._nodes[0, 2] * x_coefficient
        self._pool[choice]._nodes[0, 2] *= x_coefficient
        self._pool[choice]._nodes[1, 2] *= y_coefficient

    def plot(self):
        # ziskej hodnoty z dictionary
        num_to_plot = 4
        fig = plt.figure()
        for index in range(num_to_plot):
            ax = fig.add_subplot(1,4, index + 1)
            ax.set_title("Candidate {}".format(index))
            # vezmi num_to_plot nejlepsich kandidatu
            pool = self._pool[index]
            plot_dict = pool._plot_dict
            stress = pool._stress
            xi = plot_dict['xi']
            xj = plot_dict['xj']
            yi = plot_dict['yi']
            yj = plot_dict['yj']
            xinew = plot_dict['xinew']
            xjnew = plot_dict['xjnew']
            yinew = plot_dict['yinew']
            yjnew = plot_dict['yjnew']
            stress_normed = plot_dict['stress_normed']
            F_numnodex2 = plot_dict['F_numnodex2']
            numnode = plot_dict['numnode']


            #stress, numnode, xi, xj, yi, yj, xinew, xjnew, yinew, yjnew, stress_normed, F_numnodex2
            for r in range(3):
                x = (xi[r], xj[r])
                y = (yi[r], yj[r])
                line = plt.plot(x, y)
                plt.setp(line, ls='-', c='black', lw='1', label='orig')

                xnew = (xinew[r], xjnew[r])
                ynew = (yinew[r], yjnew[r])
                linenew = plt.plot(xnew, ynew)
                plt.setp(linenew, ls='-', c='c' if stress[r] > 0 else 'crimson', lw=1 + 20 * stress_normed[r],
                     label='strain' if stress[r] > 0 else 'stress')

            for r in range(numnode):
                plt.annotate(F_numnodex2[r],
                             xy=(xi[r], yi[r]), xycoords='data',
                             xytext=(np.sign(F_numnodex2[r]) * -50), textcoords='offset pixels',
                             arrowprops=dict(facecolor='black', shrink=0, width=1.5, headwidth=8),
                             horizontalalignment='right', verticalalignment='bottom')
                # print("N"+str(i+1)+" = "+ str(np.round(N[i] /1000,3)) +" kN")
            plt.axis('equal')

        plt.show()