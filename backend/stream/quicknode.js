function main(stream) {
    try {
        // If stream is configured with metadata in the body, the data may be nested under a `data` key
        const data = stream.data ? stream.data[0] : stream[0]

        const addresses = [
            '0xc70df87e1d98f6a531c8e324c9bcec6fc82b5e8d',
            '0xb449701a5ebb1d660cb1d206a94f151f5a544a81',
            '0x5beb759f7769193a8e401bb2d7cad22bacb930d5',
        ]
        var addressSet = new Set(addresses.map(address => address.toLowerCase()))

        var filterTransactions = []
        var matchingTransactions = []
        var matchingReceipts = []
 
        if (Array.isArray(data.receipts) && data.receipts.length) {
            data.receipts.forEach(receipt => {
                let  receiptMatches =
                    receipt.logs &&
                    receipt.logs.some(
                        log =>
                            log.address &&
                            addressSet.has(log.address)
                    )
                if (receiptMatches) {
                    filterTransactions.push(receipt.transactionHash)
                }
            })
        }

        if (!filterTransactions.length) {
            return null
        }

        data.block.transactions.forEach(transaction => {
            if (filterTransactions.includes(transaction.hash)) {
                matchingTransactions.push(transaction)
            }
        })

        data.receipts.forEach(receipt => {
            if (filterTransactions.includes(receipt.transactionHash)) {
                matchingReceipts.push(receipt)
            }
        })

        return {
            block: data.block.number,
            timestamp: data.block.timestamp,
            transactions: matchingTransactions,
            receipts: matchingReceipts,
        }
    } catch (e) {
        return { error: e.message }
    }
}