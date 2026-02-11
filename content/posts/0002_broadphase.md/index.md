---
title: Broad phase algorithms and data structures
desc: Trees, sweeps and how to lie with big O
date: 2026-02-10
math: true
# draft: true
---

An important part of game engines and various geospatial software is the notion
of overlap between objects. Objects are represented using data (in games
entities have a position and a collision shape, while in databases entities are
multimodal data points). We want to find collision between these objects, or to
search for nearest neighors of any single object.

The obvious solution of scanning every pair (or every n-tuple) is too slow for
real world data, and so we need to find a way to quickly prune false negatives
or group potential candidates together. I will cover some of these solution in
this article.

## Metric spaces 

We are all adults here so let's formalize things.
A _metric space_ is a set of objects $M$, which can be anything,
and a distance function $d : M \times M \to \mathbb{R}$.
So if you have a set of any _thing_ of some type, 
and you can define a "distance" between any two things, you've got a metric space.
The distance function is called a _metric_, and you use this metric to measure
things beyond the distances between two objects in the set.
The metric must satisfy these properties:
- $d(x, x) = 0$
- $d(a, b) > 0, \quad a \neq b$
- $d(a, b) + d(b, c) \ge d(a, c)$

The Euclidean space is a classic example of a metric space. It's how we percieve
the world, it's what games use, and it's what we normally think of when we say
"space".

In more complicated scenarios where you have data of different type and none of
them represent position in real space, you have to get creative. But as long as
you can measure the distance between these two objects and this measure satisfies
the above properties, it's a metric space, no matter how unintuitive the measure
function itself may be.

This article will deal with the Euclidean space because it's primarilly written
for game engines and because it's easy and intuitive to visualize.

## Problem formulation

Let _entity_ be a type representing an object in two-dimensional Euclidean space
with a volume larger than $0$. I've picked two dimensions for simplicity. Having
a volume larger than $0$ just means that the entity has a shape and is not an
inifnitely small point. Such an entity is often called a particle and they
simplify things, but are not practial in the general sense.

The task is to find the set of pairs of entities $e_1, e_2$ whose volumes are
intersecting. This may vaguely resemble collision detection, but the entities'
velocities are ignored. We are only interested in answering this question:
_which entities are intersecting right now?_

Depending on your use case, this pair of entities can be ordered (2-tuple) or
unordered (binary set). Game engines normally deal with unordered pairs because
there's no need to process the same collision twice. In this article we
talk about unordered pairs $\\{e_1, e_2\\}$.

We know ahead of time which entity pairs can be elements of the resulting set.
Any entity can be paired up against any other entity (except for itself), so if
we have $n$ entities, the total number of possible pairs is $n \choose 2$.

It's important to establish the concept of _bounding volumes_. Take a look at
the image below. If every entity in the scene is a star, then checking for star
intersection would require a sophisticated intersection algorithm like
Separating Axis Test.

<img src="./scene_stars.png" width="300"/> 

Percise intersection checks are part of the _narrow phase_ in collision
detection. This article deals with the _broad phase_. It's very wasteful to
always perform precise intersection algorithms on the exact shapes. We can purge
false positives by first checking for intersection of the entities' _bounding
volumes_. These volumes are often very primitive and efficient to construct and
check for intersection against.

<img src="./bounding_volume.png" width="300"/> 

Axis-aligned rectangles or circles have an $O(1)$ intersection algorithm, and
their construction is $O(N)$ for the number of points $N$ in the entity's
volume. Commonly, we can compute the bounding volume ahead of time and assume it
changes only when the entity scales, rotates or the bounding volume itself
transforms. Game engines tend to not allow the latter case, as most shapes are
aassumed to be rigid i.e. undeformable.

This article uses axis-aligned rectangles for the bounding volumes. Circles are
more efficient for shapes with a similar span in both axes, otherwise ellipses
can be used. However, the strategies discussed in this article mostly deal with
the very edge of an entity's volume in the $x$ or $y$ axis, and so it seems
natural to go with rectangles.

