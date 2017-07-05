from datetime import datetime
##from collections import OrderedDict, deque
import collections
import numpy as np
import heapq

class User_Network:

	def __init__(self, D, T):
		'''
		Initialize a User network object to check for anomalous purchases.

		D = number of degrees in User network to check
		T = number of historical purchases to check
		'''
		self.D = D
		self.T = T
		self.Userid = {} # dictionary of integer ids to User objects


	## Process individual events streaming in from input json file

	def add_batch_event(self, event_log):
		'''
		Add an batch event from the batch_log to User Network.
		
		event_log: Dictionary of parsed json purchase event.
		return: None
		'''
		event_type = event_log['event_type']
		if event_type == 'purchase':
			self.add_purchase(event_log)
		elif event_type == 'befriend':
			self.add_befriend(event_log)
		elif event_type == 'unfriend':
			self.add_unfriend(event_log)
		else:
			raise ValueError("Unknown event type", event_type)


	def add_streaming_event(self, event_log):
		'''
		Add in a streaming event from the stream log to this network.
		Check if this event is an anomalous purchase.

		event: Dictionary representing the parsed json event to add.
		return: an collections.OrderedDict representing an anomalous event if an anomaly
		is detected; boolean False otherwise.
		'''
		event_type = event_log['event_type']
		if event_type == 'purchase':
			anomaly = self.is_anomaly(event_log)
			self.add_purchase(event_log)
			if anomaly:
				mean, std = anomaly
				anomal_string = collections.OrderedDict([ ('event_type', 'purchase'),
							('timestamp', event_log['timestamp']), 
							('id', event_log['id']), 
							('amount', event_log['amount']),
							('mean', str('%.2f'%(mean))),
							('sd', str('%.2f'%(std)))
							])
				return anomal_string				
			return False
		elif event_type == 'befriend':
			self.add_befriend(event_log)
		elif event_type == 'unfriend':
			self.add_unfriend(event_log)
		else:
			raise ValueError("Unknown event type", event_type)


	## update network triggered by different events

	def add_purchase(self, event_log):
		'''
		Update network state with purchase event.

		event_log: Dictionary of parsed json representing purchase event.
		return: None
		'''
		# update user information
		id = event_log['id']
		timestamp = event_log['timestamp']
		amount = event_log['amount']

		if id in self.Userid:
			user = self.Userid[id]
			user.purchase(timestamp, amount)
			# update user object
		else:
			new_user = User(id, self.T)
			new_user.purchase(timestamp,amount)
			self.Userid[id] = new_user
			# create new user object and add to user map
		return (timestamp,amount)


	def add_befriend(self, event_log):
		'''
		Update network state with befriend event.

		event_log: Dictionary of parsed json representing befriend event.
		return: None
		'''
		id1 = event_log['id1']
		id2 = event_log['id2']
		if id1 not in self.Userid:
			user1 = User(id1, self.T)
			self.Userid[id1] = user1
		else:
			user1 = self.Userid[id1]

		if id2 not in self.Userid:
			user2 = User(id2, self.T)
			self.Userid[id2] = user2
		else:
			user2 = self.Userid[id2]

		user1.befriend(id2)
		user2.befriend(id1)
		return user1, user2


	def add_unfriend(self, event_log):
		'''
		Update network state with unfriend event.

		event_log: Dictionary of parsed json representing unfriend event.
		return: None
		'''
		id1 = event_log['id1']
		id2 = event_log['id2']

		user1 = self.Userid[id1]
		user2 = self.Userid[id2]
		user1.unfriend(id2)
		user2.unfriend(id1)
		return user1, user2


	### Fns used to check for anomalies

	def get_friends_list(self, user):
		'''
		Gets the list of all friends in a user's dth degree network, where D is
		 defined by self.D, the degree of the network.

		user: integer id of user to get friends list from.
		return: list of all integer ids of people in user's dth degree network
		'''
		# breadth first search
		count = 0
		friends_list = set()
		queue = [(user, 0)]
		while queue != []:
			# print queue
			curr_user, depth = queue.pop(0)
			if curr_user not in friends_list:
				if depth < self.D+1:
					friends_list.add(curr_user)
					for friend in self.Userid[curr_user].friends:
						queue.append((friend,depth+1))
		friends_list.remove(user)
		return friends_list


	def get_purchases(self, friends_list):
		'''
		Gets the most recent purchases out of the users in friends_list,
		 where self.T is the number of purchases to consider.

		friends_list: a list of integer ids of users in the network.
		return: a list of tuples of (timestamp, rank, amount) for the T most
		 recent purchases in the network.
		'''
		p = []
		for friend in friends_list:
			p.extend(self.Userid[friend].purchases)
		return heapq.nlargest(self.T, p)


	def is_anomaly(self, purchase_event):
		'''
		Check if a given purchase is anomalous given self.T and self.D.
		An event is anolalous if it is more than 3 standard devations above the
		 mean of the last T purchases in the users dth degree user social network.
		Events for which the network has fewer than 2 purchases are not flagged
		 as anomalous.

		event: Dictionary representing parsed json event.
		return: Tuple of average and std of previous events if the event is
		 anomalous; False if the event is not anomalous.
		'''
		id = purchase_event['id']
		amount = float(purchase_event['amount'])
		user = self.Userid[id]
		friends_list = self.get_friends_list(id)
		purchases = self.get_purchases(friends_list)
		if len(purchases) >= 2:
			amounts = [float(n) for _, _, n in purchases]
			mean = np.mean(amounts)
			std = np.std(amounts)
			if amount > mean + 3 * std:
				return (mean, std)
		return False



class User:
	def __init__(self, id, max_purchases):
		self.id = id # int of user id
		self.friends = set() # set of ints of friends' user ids
		self.purchases = collections.deque(maxlen=max_purchases) # list of tuples (timestamp, rank, amount)
		# self.purchases = []

	def befriend(self, user):
		self.friends.add(user)

	def unfriend(self, user):
		self.friends.remove(user)

	def purchase(self, timestamp, amount):
		# A purchase is stored as a tuple (timestamp, rank, amount).
		# Timestamp and amount are taken from the original json event.
		# Rank is used to break ties for events with the same timestamp.
		ts = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
		if self.purchases:
			last_purchase = self.purchases[-1]
			last_purchase_ts = last_purchase[0]
			if ts == last_purchase_ts:
				last_purchase_rank = last_purchase[1]
				rank = last_purchase_rank + 1
			else:
				rank = 0
			new_purchase = (ts, rank, amount)
		else:
			new_purchase = (ts, 0, amount)
		self.purchases.append(new_purchase)

		


