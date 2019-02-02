class Mention {
	/**
	* @class Mention
	* @classdesc Allows using a symbol to display options
	*
	* @param {Object} settings - Options to initialize the component with
	* @param {HTMLElement} settings.input - The textarea to watch {@link Component#input}
	* @param {HTMLElement} settings.optionList - Element to display options when matched {@link Component#optionList}
	* @param {Array} settings.options - Array of options. Options can have properties {@link Component#options}
	* @param {String} [settings.symbol="@"] - The symbol that initials the option list {@link Component#symbol}
	* @param {Function} [settings.match] - The function used to match options {@link Component#match}
	* @param {Function} [settings.template] - The template function outputs the innerHTML of the optionlist {@link Component#template}
	*/
   constructor(settings) {
      this.options = settings.options || []
      this.input = settings.input
      this.reverse = settings.reverse

      this.symbol = settings.symbol || '@'
      this.cursorPosition = 0
      this.hover = 0
      this.showingOptions = false
      this.upDownStay = 0
      this.wordAtCursor = {}
      this.update = settings.update || function(){}
      this.match = settings.match || this.match
      this.template = settings.template || this.template
      this.startsWith = settings.startsWith || this.startsWith
      this.html = {
         input: undefined,
         display: undefined,
         wrapper: undefined,
         optionsList: undefined,
         options: [],
         spans: [] }
      this.setupHTML()
      this.listen()
   }

	/**
	* Function used to match options based on the word
	* @param {String} [word] - The current word ex. @test
	* @param {String} [option] - The options being looped
	* @return {boolean} - If the word matches the option
	*/
   match(word, option) {
      var optionText = option.name || option
      return optionText.toLowerCase() == word.toLowerCase()
   }

	/**
	* Called to see if option starts with the word
	* @param {String} [word] - The current word ex. @test
	* @param {String} [option] - The options being looped
	* @return {boolean} - If the word starts with the option
	*/
   startsWith(word, option) {
      var optionText = option.name || option
      return optionText.toLowerCase().startsWith(word.toLowerCase())
   }

	/**
	* Function returns the template (innerHTML) that will be used for each option
	* @param {String} [option] - The options being looped
	* @return {String} - The innerHTM
	*/
   template(option) {
      return option.name || option
   }

	/**
	* Sets up the HTML. Wrapper, Display, OptionsList, Options
	*/
	setupHTML() {
      this.html.input = this.input

      // Global wrapper
      this.html.wrapper = document.createElement('div')
      this.html.wrapper.classList.add('mention-wrapper')
      this.html.input.parentElement.insertBefore(this.html.wrapper, this.html.input)
      this.html.wrapper.appendChild(this.html.input)

      // Options
      this.html.optionsList = document.createElement('div')
      this.html.optionsList.classList.add('mention-options')
      this.html.wrapper.appendChild(this.html.optionsList)
      if(this.reverse) {
         this.html.optionsList.classList.add('mention-options-reverse')
         this.html.wrapper.insertBefore(this.html.optionsList, this.html.wrapper.firstChild)
      }

      for(var option of this.options) {
         var optionElement = document.createElement('div')
         optionElement.classList.add('mention-option')
         optionElement.innerHTML = this.template(option)
         optionElement.setAttribute('mentiondata', JSON.stringify(option))
         this.html.options.push(optionElement)
         this.html.optionsList.appendChild(optionElement)
      }
   }

	/**
	* Begins listening for events on the input and options
	*/
   listen() {
      this.html.input.addEventListener('input', () => { this.onEventInput() })
      this.html.input.addEventListener('keydown', (e) => { this.onEventKeyDown(e) })
      this.html.input.addEventListener('keyup', (e) => { this.onEventKeyUp(e) })
      this.html.options.forEach((o) => {
         o.addEventListener('click', (e) => { this.onEventOptionClick(e.target) })
      })
   }

	/**
	* Called when  on input.addEventListener('input')
	* @param {Event} e - the event passed
	*/
	onEventInput() {
      this.update()
	}

   /**
	* Called when  on input.addEventListener('keyup')
	* @param {Event} e - the keyboard event passed
	*/
   onEventKeyDown(e) {
      this.upDownStay = e.keyCode == 40 ? 1 : e.keyCode == 38 ? -1 : 0
      if(this.reverse) this.upDownStay *= -1
      if(this.upDownStay && this.showingOptions) e.preventDefault()
      if(e.keyCode == 13 && this.showingOptions) {
         e.preventDefault()
         var option = this.html.options.find((e) => e.classList.contains('hover'))
         if(option) this.onEventOptionClick(option)
      }
   }

   /**
	* Called when  on input.addEventListener('keydown')
	* @param {Event} e - the event passed
	*/
   onEventKeyUp() {
      this.cursorPositionChanged()
      this.setHoverOption()
   }

   /**
	* Called when option input.addEventListener('click')
	*/
   onEventOptionClick(optionEle) {
      var word = this.symbol + JSON.parse(optionEle.getAttribute('mentiondata')).name + ' '
      var splitInputValue = this.html.input.value.split('')
      splitInputValue.splice(this.wordAtCursor.index, this.wordAtCursor.word.length, word)
      this.html.input.value = splitInputValue.join('')
      this.html.input.focus()
      this.setCursorPosition(this.wordAtCursor.index + word.length + 1)
      this.toggleOptionList(false)
      this.update()
   }

   /**
   * Cursor position changed. Check for input data and toggle options
   */
   cursorPositionChanged() {
      this.cursorPosition = this.html.input.selectionStart
		this.wordAtCursor = this.readWordAtCursor({ cursorPosition: this.cursorPosition, value: this.input.value })
      this.toggleOptionList(this.wordAtCursor.word.length && this.wordAtCursor.word[0] == this.symbol)
		this.showHideOptions()
   }

	/**
	* Show/Hide the options list
	* @param {Boolean} toggle - show or hide
	*/
	toggleOptionList(toggle) {
      this.html.optionsList.classList.remove('show')
      if(toggle) this.html.optionsList.classList.add('show')
      this.showingOptions = toggle
   }

	/**
	* Loop the options and show/hide options based on match function
	*/
	showHideOptions() {
      for(var option in this.options) {
         var word = this.wordAtCursor.word.replace(this.symbol, '')
         this.html.options[option].classList.remove('show')
         if(this.startsWith(word, this.options[option])) this.html.options[option].classList.add('show')
      }
   }

	/**
	* Using up/down arrow selects the next option
	*/
   setHoverOption() {
      var viewableOptions = this.html.options.filter((e) => {
         e.classList.remove('hover')
         return e.classList.contains('show')
      })
      if(!viewableOptions.length){
         this.toggleOptionList(false)
         return
      }

      this.hover = this.upDownStay ? this.hover + this.upDownStay : 0
      if(this.hover < 0){ this.hover = viewableOptions.length - 1 }
      if(this.hover == viewableOptions.length) { this.hover = 0}
      viewableOptions[this.hover].classList.add('hover')
   }

   /**
   * Sets the cursor position in the text area
   * @param {Number} position - the position
   */
   setCursorPosition(position) {
      this.cursorPosition = position
      this.html.input.setSelectionRange(position, position);
   }

   /**
	* From the cursor positoin looks back to match the work and start/end position
	* @param {Object} data - Options to initialize the component with
	* @param {String} [data.value] - the string to search through
	* @param {Number} [data.cursorPosition] - The position of the cursor in the string
	*/
   readWordAtCursor(data) {
      var word = '', index = data.cursorPosition
      var valueWithReplacedSpecial = data.value.replace(/\n/g, ' ');

      while(index--){
         var previousCharacter = valueWithReplacedSpecial[index]
         if(previousCharacter == ' ' || index < 0) break
      }

      while(index++ < valueWithReplacedSpecial.length-1) {
         var nextCharacter = valueWithReplacedSpecial[index]
         if(nextCharacter == ' ') break
         word += nextCharacter
      }

      return { index: Math.max(index-word.length, 0), word: word }
   }

	/**
	* Loops over the input value.
	* @return {matches[]} - Array of matches { word: word, index: index word is at}
	*/
	findMatches() {
		var inputValue = this.html.input.value.split('').concat([' '])
		var words = []

		var currentWord = ''
		for(var index in inputValue) {
			var letter = inputValue[index]
			var lastLetter = inputValue[index-1] || ' '
			var lastLetterIsSpace = [' ', '\\n'].indexOf(lastLetter) > -1 || lastLetter.charCodeAt(0) == 10
			var canStartWord = letter == this.symbol && lastLetterIsSpace

			if((canStartWord || currentWord.length) && letter != ' ') currentWord += letter

			if(currentWord.length && letter == ' '){
				words.push({ word: currentWord, index: Math.max(index-currentWord.length, 0) })
				currentWord = ''
			}
		}

		return words;
	}

	/**
	* Collects all the real matches
	*/
	collect() {
		return this.findMatches().filter((word) => {
			return this.options.some((option) => {
				return this.match(word.word.replace(this.symbol, ''), option)
			})
		})
	}
}

if(typeof module != 'undefined') module.exports = Mention


var myMention = new Mention({
   input: document.querySelector('#id_comments'),
   options: assigned_to_list,


   template: function(option) {
     return '@' + option.name
   }
})


var myMention = new Mention({
   input: document.querySelector('#id_editcomment'),
   options: assigned_to_list,

   // match: function(word, option) {
   //    return option.name.startsWith(word)
   //       || option.description.toLowerCase().indexOf(word.toLowerCase()) >= 0
   // },
   template: function(option) {
     return '@' + option.name
   }
})
