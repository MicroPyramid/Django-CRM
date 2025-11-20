// Newsletter utility functions for email confirmation and management

/**
 * Generate unsubscribe link
 * @param {string} token - Confirmation token
 * @param {string} baseUrl - Base URL of the application
 * @returns {string} Unsubscribe URL
 */
export function generateUnsubscribeLink(token, baseUrl = 'https://bottlecrm.io') {
  return `${baseUrl}/unsubscribe?token=${token}`;
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} True if email is valid
 */
export function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Generate email confirmation template
 * @param {string} email - Subscriber email
 * @param {string} unsubscribeLink - Unsubscribe link
 * @returns {object} Email template with subject and body
 */
export function generateWelcomeEmail(email, unsubscribeLink) {
  return {
    subject: 'Welcome to BottleCRM Newsletter!',
    html: `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to BottleCRM Newsletter</title>
      </head>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
          <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to BottleCRM!</h1>
          <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 16px;">Thank you for subscribing to our newsletter</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 30px; border-radius: 10px; margin-bottom: 30px;">
          <h2 style="color: #333; margin-top: 0;">What to expect:</h2>
          <ul style="padding-left: 20px;">
            <li style="margin-bottom: 10px;">🚀 <strong>Product Updates:</strong> Be the first to know about new features and improvements</li>
            <li style="margin-bottom: 10px;">💡 <strong>CRM Tips:</strong> Best practices to maximize your customer relationship management</li>
            <li style="margin-bottom: 10px;">📊 <strong>Industry Insights:</strong> Stay ahead with the latest CRM trends and strategies</li>
            <li style="margin-bottom: 10px;">🎯 <strong>Exclusive Content:</strong> Guides and resources available only to subscribers</li>
          </ul>
        </div>
        
        <div style="text-align: center; margin-bottom: 30px;">
          <a href="https://bottlecrm.io/demo" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Try BottleCRM Free</a>
        </div>
        
        <div style="text-align: center; color: #666; font-size: 14px; border-top: 1px solid #ddd; padding-top: 20px;">
          <p>You're receiving this email because you subscribed to BottleCRM newsletter.</p>
          <p>
            <a href="${unsubscribeLink}" style="color: #666; text-decoration: underline;">Unsubscribe</a> | 
            <a href="https://bottlecrm.io" style="color: #666; text-decoration: underline;">Visit Website</a>
          </p>
          <p style="margin-top: 20px;">
            <strong>BottleCRM</strong> by MicroPyramid<br>
            The free, open-source CRM for startups
          </p>
        </div>
      </body>
      </html>
    `,
    text: `
      Welcome to BottleCRM Newsletter!
      
      Thank you for subscribing to our newsletter. Here's what you can expect:
      
      • Product Updates: Be the first to know about new features and improvements
      • CRM Tips: Best practices to maximize your customer relationship management  
      • Industry Insights: Stay ahead with the latest CRM trends and strategies
      • Exclusive Content: Guides and resources available only to subscribers
      
      Try BottleCRM Free: https://bottlecrm.io/demo
      
      You're receiving this email because you subscribed to BottleCRM newsletter.
      To unsubscribe, visit: ${unsubscribeLink}
      
      BottleCRM by MicroPyramid
      The free, open-source CRM for startups
      https://bottlecrm.io
    `
  };
}

/**
 * Generate newsletter template for regular updates
 * @param {any} content - Newsletter content
 * @param {string} unsubscribeLink - Unsubscribe link
 * @returns {object} Newsletter template with subject and body
 */
export function generateNewsletterTemplate(content, unsubscribeLink) {
  const { subject, headline, articles = [], ctaText = 'Learn More', ctaLink = 'https://bottlecrm.io' } = content;
  
  const articlesHtml = articles.map(/** @param {any} article */ article => `
    <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #667eea;">
      <h3 style="margin: 0 0 10px 0; color: #333;">${article.title}</h3>
      <p style="margin: 0 0 15px 0; color: #666; line-height: 1.6;">${article.excerpt}</p>
      <a href="${article.link}" style="color: #667eea; text-decoration: none; font-weight: 500;">Read more →</a>
    </div>
  `).join('');
  
  return {
    subject,
    html: `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>${subject}</title>
      </head>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
          <h1 style="color: white; margin: 0; font-size: 24px;">${headline}</h1>
        </div>
        
        <div style="margin-bottom: 30px;">
          ${articlesHtml}
        </div>
        
        <div style="text-align: center; margin-bottom: 30px;">
          <a href="${ctaLink}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">${ctaText}</a>
        </div>
        
        <div style="text-align: center; color: #666; font-size: 14px; border-top: 1px solid #ddd; padding-top: 20px;">
          <p>You're receiving this email because you subscribed to BottleCRM newsletter.</p>
          <p>
            <a href="${unsubscribeLink}" style="color: #666; text-decoration: underline;">Unsubscribe</a> | 
            <a href="https://bottlecrm.io" style="color: #666; text-decoration: underline;">Visit Website</a>
          </p>
          <p style="margin-top: 20px;">
            <strong>BottleCRM</strong> by MicroPyramid<br>
            The free, open-source CRM for startups
          </p>
        </div>
      </body>
      </html>
    `
  };
}
