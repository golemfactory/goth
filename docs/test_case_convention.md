# Test Case Specification Considerations

This article is to illustrate a proposed convention for the Test Harness framework which would allow low level interaction with Golem APIs, but at the same time provide a reasonable level of test case readability.

```
    # ...use the docker instrumentation utils to spin up the test network of selected topology...

    requestor = RequestorProbe(requestorUrl)
    
    # Perform Market negotiation

    demand = Demand(
        properties = {
            "" : "",
            "" : "",
        },
        constraints = "(
            
        )"
    );

    subscriptionId = requestor.market.subscribe(demand)

    offerProposal = requestor.market.collect(subscriptionId).firstOrDefault()

    assertTrue(offerProposal != null)
    assertEqual(offerProposal.properties["somepropname"], "expected value")

    requestor.cli.waitUntil("some regexp for expected log line")
    requestor.cli.mustNotHave("some regexp for ERROR")

    agreementId = requestor.market.createAgreement(offerProposal)

    requestor.market.confirmAgreement(agreementId)

    agreementResponse = requestor.market.waitForAgreement(agreementId)

    assertEqual(agreementResponse, Agreement.OK)

    # Move on to Activity 

    activityId = requestor.activity.createActivity(agreementId)

    assertTrue(activityId != null)

    exeScript = ExeScript(
        [
            ExeCommand( Command.Deploy ),
            ExeCommand( Command.Start ),
            ExeCommand( Command.Transfer, ["gft://localfile", "container:/input/input_file"] ),
            ExeCommand( Command.Run, ["arg1", "arg2"] ),
            ExeCommand( Command.Transfer, ["container:/output/output_file", "gft://result" ] ),
        ]
    )

    batchId = requestor.activity.exec(exeScript)

    exeResults = requestor.activity.getExecBatchResult(batchId)

    foreach exeResult in exeResults
        assertTrue(exeResult.Result = OK)

    # also validate payment events

    invoiceEvent = requestor.payment.events.firstOrDefault(event => event.type = InvoiceReceived)

    assertNotNull(invoiceEvent)

    requestor.payment.acceptInvoice(invoiceEvent.invoiceId)

    requestor.cli.waitUntil("some regexp for payment confirmation line")


```
