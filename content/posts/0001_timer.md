---
title: Immediate mode timer in games
desc: A surprisingly useful thing game engines do wrong
date: 2025-10-23
---

Quick: how do you perform some code in your game after a certain amount of time?
Well, that depends on the game engine you use.

In Unity, you use Coroutines.

```C#
private bool canGetHit = true;

void OnGetHit()
{
    StartCoroutine(BecomeInvincible(5));
}

IEnumerator BecomeInvincible(float time) {
    canGetHit = false;
    yield return new WaitForSeconds(time);
    canGetHit = true;
}
```

In Godot, you use the Timer node.

```gdscript
var can_get_hit: bool = true


func on_get_hit():
    become_invincible(5.0)


func become_invincible(time: float):
	can_get_hit = false
	var timer = get_tree().create_timer(time)
    timer.timeout.connect(_on_timer_timeout)


func _on_invicible_timer_timeout():
	can_get_hit = true
```

In Unreal Engine 5, there's the TimerManager:

```c++
/// .h

bool canGetHit = true;
FTimerHandle invincibilityTimer;

void OnGetHit();
void OnInvincibilityTimerEnd();

/// .cpp

void MyActor::OnGetHit() {
    BecomeInvincible(5.0f);
}

void MyActor::BecomeInvincible(float time) {
    canGetHit = false;
    GetWorldTimerManager().SetTimer(invincibilityTimer, this, &YourClass::OnGetHit, time, false);
}

void MyActor::OnInvincibilityTimerEnd() {
    canGetHit = true;
}
```

In GameMaker, you use Alarms or Time Sources and so on and so on.

The one thing in common between all these approaches are _callbacks_.

You create a timer, tell it to go off in _this many_ seconds or frames and you tell it
which function to invoke when the timer goes off. It's a declarative approach of "I want to
do this at this time, let the engine take care of the rest".

---

I propose a different solution, inspired by immediate mode graphics libraries.
The big idea is for you (your class, your component, your node, whatever) to own the timer,
to update the timer and to query the timer _explicitly_:

```c++
struct Timer {
    float current, start;

    Timer(float start_seconds) {
        start = start_seconds;
        current = start;
    }

    bool update(float dt) {
        current -= dt;
        if current <= 0 {
            current = 0;
            return true;
        }
        return false;
    }

    void reset() { 
        current = start; 
    }

    void reset_with(float new_start_seconds) {
        start = new_start_seconds;
        reset();
    }
};
```

And then you use it like this (pseudo-engine):

```c++
Timer invincibility_timer = Timer()
bool can_get_hit = true;

void update() {
    if (invincibility_timer.update(Game::delta_time)) {
        can_get_hit = true;
    }
}

void on_get_hit() {
    can_get_hit = false;
    invincibility_timer.reset();
}
```

At first glance, we lose a lot of things:
1. You have to keep track of all the timers yourself
2. The code that runs when the timer goes off is defined at a different place from where it's activated
3. The usage example above is not 1:1 to the examples of established game engines

---

I argue that these drawbacks are benefits in disguise:

**(1)** -- Yes, you have to keep track of all the timers, but they are an integral part
of your entity/actor/component/node anyway. Why shouldn't a player keep track of
when he's going to stop being invincible?

Now, one could argue that all game engines mitigate this issue in some part. And
in fact, you _can_ know the elapsed time in Unity or Godot. And in UE5 you're
already keeping a handler for the timer. But that's just it - you don't own the
timer itself. The timer is part of the engine's runtime even though it only
concerns your script. In Godot's case, it creates a brand new node that your
script has no control over (unless you explicitly keep a reference to it, but
you should prefer using signals).

By having an explicit timer like this, you can be sure that multiple attempts to
start the timer override each other, instead of stacking indefinitely. If you
really want them to stack, create a pool of timers. Abstract it into a
`TimerMulti` struct with the same API as a `Timer`. It's _that_ simple.

**(2)** -- Yes, you can't know what's gonna happen when the timer goes off just
by looking at the line of code that starts the timer, but what you gain is full
control of when exactly the timer's invocation logic begins -- even at the
instruction level.

If you rely on the engine to update timers for you, you are subject to
unpredictable concurrency. In software such as games (or in this case game
engines), which I see as virtual operating systems with domain-specific
scheduling, state is large and state changes are instanteneous and ephemeral.

In Unity, coroutine yield commands execute between `Update` and `LateUpdate`. If
the result of the coroutine changes some critical part of your component's state
such that it's not compatible with a state change in `Update`, then you have to
either do a bulk state change inside the coroutine or in `LateUpdate`. 

If you have multiple coroutines within a same GameObject, you can't control the
order of their execution. If you have "stacking" coroutines, you're really
screwed. Good luck debugging that.

With an explicit timer, you know exactly when the timer ticks, when the timer
goes off, how different timers interact, nesting timers makes sense because the
inner timer is conditional on the outer timers and so on.

**(3)** -- The caveats of my usage example are many, and my proposed timer API
may not be everyone's cup of tea, but the primary idea is:

```c++
if (timer.update(Game::delta_time)) {
    // Do stuff.
}
```

How do you do a looping timer?

```c++
if (timer.update(Game::delta_time)) {
    timer.reset();
    // Do stuff.
}
```

What if we want it to loop 4 times? First we need a struct that counts _ticks_
instead of _seconds_:

```c++
struct TickTimer {
    ...
    bool update() { ... }
    bool finished() { ... }
};
```

and then:

```c++
tick_timer = TickTimer(4);

...

if (timer.update(Game::delta_time) && !tick_timer.finished()) {
    timer.reset();
    tick_timer.update();

    // Do stuff.
}
```

What if I want to trigger the timer only once instead of whenever it's finished:

```c++
struct Timer {
    bool update_now(float dt) {
        return current > 0 && update(dt);
    }
}
```

I know I haven't actually provided an answer to this counterargument, but there
isn't any point to address it either, it's just a matter of implementation.

---

Callbacks are a "don't call us -- we'll call you" type of deal. Using callbacks
for something like a timer, which in games and game engines should
_de facto_ be a primitive data type, is wrong.

Whenever I start a new project in Unity or Godot, the first thing I do is create
a custom Timer class like the one above. You may not feel convinced at first,
but it makes all the difference in the world once you have to debug.

The explicit, imperative, immediate, stupid-simple approach to timers like this
inverts the control back to your code. The timer _is_ the game code.