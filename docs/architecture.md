# Architecture idea

This document describes a previous testing framework I have build using Selenium.
We can use this as a base for deciding on how we want to shape this testing framework.

## Introduction

My previous company, suitsupply.com had over 30 developers working on a single website.
As DevOps team we where asked to setup a selenium testing suite where the developers and QA where in control of maintaining the tests.
With a team of 4 we developed said framework.

## Setup

### QA side, non developer users
We wanted the QA team to have a central role in this project, since they are the ones providing the scenarios and checking the results.
The idea was for them to write the test scenarios in simple "static" or "functional" Javascript code.
For example:
```
const variant = site.product_page.get_variant('size=42');
site.product_page.add_to_cart(variant)
site.cart.assert_added(variant)
```

As you can see all they had to use ( and know ) was the well documented `site` object / class.
This always contained 3 levels: `site`, page (or component ) and actions.
```
site.<page_or_component>.<action>()
```
This documentation was enforced by code styles, and automatically build/published on each new commit.

This way they could easily convert the textual scenario's into code.
And when running the tests they knew exactly what step failed, since each function called above would log its start and finish.

Now the QA responsibility is clear lets dive in one level deeper, where did the `site` class get maintained

### Web developer side

The `site` class was maintained by the web-developers, with each feature they build or change they also had to update the `site` class to match the expected behaviour.
Unless new arguments where added, all old tests would still work properly when both the `site` class and the actual website got updated at the same time.

Here we ran into a big challenge, the QA had to be able to write "static" code while the libraries used in the background had a complex asynchronous structure.
To add to this with animations and fancy late loading caused a lot of problems.
Last but not least not all the libraries expected the same structure of code to be written, making it confusing to use them together.

To assist the developers in making this easier we move to the guts of the framework.

### DevOps developers side

To help the web-developers deliver new pages and actions quickly we wrapped the used libraries in a super utility library ( SeleniumJS ).
This enabled us to unify all function calls into clean asynchronous "Promises" and allow the developers to write clean code.

We used the same documentation enforcement, with separate generation and publication from the QA documentation.
As discussed before the regular log levels would print the function start / end of the QA called static functions.
When lowering the level the web-developers could see the steps of the SeleniumJs library.
The library handled all the "waiting for animations" and "late loading" of the website. Allowing developers to focus on the actions and pages instead of the complexity of Selenium.

### Workshops

After weekly workshops with the web-developers and the QA we could transfer the maintenance of this project to them. Freeing the DevOps team up to build servers again.

## Application to yagna

For Yagna I think this could be applied to level 1 and above, for level 0 I think it is too much ground work.

We can make the `yat` ( Yagna Tester) class containing all the different API's, like `yat.market` and `yat.requestor_deamon`.
Under the hood they can use `pexpect` and `MITM` to handle the actions and assertions.
When using these libraries directly gets too complex we can decide to wrap them in a "super utility library".

This structure would also allow for mocking of API's. The same scenario could be ran with no mocks at all, or mocking all but one.
Then we can test each component separately first, and then when put all together.
All using the same "scenario's" / test files / QA written static functions.
