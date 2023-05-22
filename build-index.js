// ref https://lunrjs.com/guides/index_prebuilding.html
var lunr = require('lunr'),
    stdin = process.stdin,
    stdout = process.stdout,
    buffer = []

stdin.resume()
stdin.setEncoding('utf8')

stdin.on('data', function (data) {
    buffer.push(data)
})

// Ref https://github.com/olivernn/lunr.js/blob/aa5a878f62a6bba1e8e5b95714899e17e8150b38/lib/stop_word_filter.js#L43
customStopWordFilter = lunr.generateStopWordFilter(['li'])  // to exclude <li>
lunr.Pipeline.registerFunction(customStopWordFilter, 'customStopWordFilter')

stdin.on('end', function () {
    // modified to exclude "/" "<" ">"
    lunr.tokenizer.separator = /[\s\-\/<>’]+/
    var documents = JSON.parse(buffer.join(''))
    var idx = lunr(function () {
        this.ref('id')
        this.field('title')
        this.field('articles')
        this.field('tags')
        this.field('category')
        this.metadataWhitelist = ['position']
        this.pipeline.before(lunr.stopWordFilter, customStopWordFilter)

        documents.forEach(function (doc) {
            this.add(doc)
        }, this)
    })
    stdout.write(JSON.stringify(idx))
})
