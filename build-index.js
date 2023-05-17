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

stdin.on('end', function () {
    // modified to exclude "/" "<" ">"
    lunr.tokenizer.separator = /[\s\-\/<>]+/
    var documents = JSON.parse(buffer.join(''))
    var idx = lunr(function () {
        this.ref('id')
        this.field('title')
        this.field('articles')
        this.field('tags')
        this.field('category')
        this.metadataWhitelist = ['position']

        documents.forEach(function (doc) {
            this.add(doc)
        }, this)
    })
    stdout.write(JSON.stringify(idx))
})
